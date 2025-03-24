import os
import json
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
API_KEY = os.getenv("API_KEY")
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")
STATE_FILE = "data/course_state.json"

if not all([OPENAI_API_KEY, TWILIO_AUTH_TOKEN, API_KEY]):
    raise ValueError("Required environment variables are missing")

# Configure OpenAI
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize Flask and rate limiter
app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

# Twilio validator
twilio_validator = RequestValidator(TWILIO_AUTH_TOKEN)

def validate_twilio_request(f):
    """Decorator to validate that requests come from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get request URL
        url = request.url
        # Get POST parameters
        post_params = request.form
        # Get X-Twilio-Signature header
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Validate request
        if not twilio_validator.validate(url, post_params, signature):
            return 'Invalid request signature', 403
            
        return f(*args, **kwargs)
    return decorated_function

def require_api_key(f):
    """Decorator to validate API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')
        if not provided_key or provided_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_ip(f):
    """Decorator to validate IP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ALLOWED_IPS and request.remote_addr not in ALLOWED_IPS:
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated_function

def ensure_data_dir():
    """Ensures the data directory exists"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

def load_course_info() -> dict:
    """Safely loads course information"""
    ensure_data_dir()
    try:
        if not os.path.exists(STATE_FILE):
            return {"schedule": "", "syllabus": "", "updates": ""}
        
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"schedule": "", "syllabus": "", "updates": ""}
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"schedule": "", "syllabus": "", "updates": ""}

def save_course_info(info: dict) -> bool:
    """Safely saves course information"""
    ensure_data_dir()
    try:
        # Validate dictionary structure
        required_keys = {"schedule", "syllabus", "updates"}
        if not all(key in info for key in required_keys):
            return False
        
        # Create backup before saving
        if os.path.exists(STATE_FILE):
            backup_file = f"{STATE_FILE}.bak"
            os.replace(STATE_FILE, backup_file)
        
        # Save new content
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving course info: {e}")
        return False

# Global course information
global_course_info = load_course_info()

# User states
class State(TypedDict):
    messages: Annotated[list, add_messages]
    schedule: str
    syllabus: str
    updates: str
    last_update: datetime

user_states: dict[str, State] = {}

# Configure LangGraph
graph_builder = StateGraph(State)
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

def chatbot(state: State):
    """Processes user messages"""
    try:
        last_message = state["messages"][-1]
        query = last_message.get("content", "") if isinstance(last_message, dict) else last_message.content

        course_info = (
            f"Schedule: {state.get('schedule', 'Not available')}\n"
            f"Syllabus: {state.get('syllabus', 'Not available')}\n"
            f"Updates: {state.get('updates', 'Not available')}\n"
        )
        
        prompt = f"""Student query: {query}
        
        Course information:
        {course_info}
        
        Instructions:
        1. Respond concisely and professionally
        2. If information is not available, clearly indicate it
        3. Do not invent information not present in the context
        4. If the query is not course-related, indicate that you can only help with course topics
        """
        
        response = llm.invoke([{"role": "user", "content": prompt}])
        return {"messages": [response]}
    except Exception as e:
        logging.error(f"Error in chatbot: {e}")
        return {"messages": [{"role": "assistant", "content": "Sorry, there was an error processing your query. Please try again."}]}

# Configure the graph
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

def get_user_state(sender: str) -> State:
    """Gets or initializes a user's state"""
    now = datetime.now()
    if sender not in user_states or (now - user_states[sender]["last_update"]) > timedelta(hours=24):
        user_states[sender] = {
            "messages": [],
            "schedule": global_course_info.get("schedule", ""),
            "syllabus": global_course_info.get("syllabus", ""),
            "updates": global_course_info.get("updates", ""),
            "last_update": now
        }
    return user_states[sender]

def is_course_related(query: str) -> bool:
    """Determines if a query is course-related"""
    keywords = {
        "course", "class", "exam", "syllabus", "schedule",
        "update", "university", "subject", "topic",
        "content", "professor", "homework", "practice", "evaluation"
    }
    query_words = set(query.lower().split())
    return bool(keywords & query_words)

@app.route("/whatsapp", methods=["POST"])
@validate_twilio_request
@limiter.limit("30/minute")
def whatsapp_bot():
    """WhatsApp bot endpoint"""
    try:
        sender = request.form.get("From")
        message_body = request.form.get("Body", "").strip()
        
        if not sender or not message_body:
            return "Bad Request", 400
        
        resp = MessagingResponse()
        
        if not is_course_related(message_body):
            resp.message("This bot is only for course-related topics.")
            return str(resp)
        
        state = get_user_state(sender)
        state["messages"].append({"role": "user", "content": message_body})
        
        response_text = ""
        for event in graph.stream(state):
            if isinstance(event, dict) and "messages" in event:
                messages = event["messages"]
                if messages and isinstance(messages[-1], dict):
                    response_text = messages[-1].get("content", "")
        
        if not response_text:
            response_text = "Sorry, I couldn't process your query. Please try again."
        
        state["messages"].append({"role": "assistant", "content": response_text})
        resp.message(response_text)
        return str(resp)
        
    except Exception as e:
        logging.error(f"Error in whatsapp_bot: {e}")
        return "Internal Server Error", 500

@app.route("/update_course", methods=["POST"])
@require_api_key
@validate_ip
@limiter.limit("10/minute")
def update_course():
    """Course information update endpoint"""
    try:
        new_data = request.get_json()
        if not new_data or not isinstance(new_data, dict):
            return jsonify({"error": "Invalid data format"}), 400
        
        # Validate fields
        valid_fields = {"schedule", "syllabus", "updates"}
        if not any(field in new_data for field in valid_fields):
            return jsonify({"error": "No valid fields to update"}), 400
        
        # Update only provided fields
        for key in valid_fields:
            if key in new_data:
                value = new_data[key].strip()
                if value:
                    if global_course_info.get(key):
                        global_course_info[key] = f"{global_course_info[key]}\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {value}"
                    else:
                        global_course_info[key] = value
        
        if save_course_info(global_course_info):
            return jsonify({"message": "Course information updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to save course information"}), 500
            
    except Exception as e:
        logging.error(f"Error in update_course: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure data directory exists
    ensure_data_dir()
    
    # Run in development mode
    app.run(host="127.0.0.1", port=8000, debug=False)

