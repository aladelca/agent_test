from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, logger

class LLMService:
    def __init__(self):
        """Initializes the LLM service."""
        self.llm = ChatOpenAI(model_name=LLM_MODEL, temperature=LLM_TEMPERATURE)

    async def identify_course(self, user_input: str, available_courses: list) -> str:
        """Identifies the most similar course from user input."""
        try:
            prompt = f"""Actúa como un asistente que ayuda a identificar el curso más similar.

            CURSOS DISPONIBLES:
            {available_courses}

            INPUT DEL USUARIO: "{user_input}"

            INSTRUCCIONES:
            1. Analiza el input del usuario y compáralo con la lista de cursos
            2. Considera variaciones en el nombre, abreviaturas comunes y errores típicos
            3. Si encuentras una coincidencia razonable, devuelve el nombre exacto del curso
            4. Si no hay coincidencia clara, responde "NO_MATCH"

            RESPONDE SOLO CON EL NOMBRE EXACTO DEL CURSO O "NO_MATCH":"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error in course identification: {e}")
            return "NO_MATCH"

    async def identify_module(self, user_input: str) -> str:
        """Identifies the most similar module from user input."""
        try:
            prompt = f"""Actúa como un asistente que ayuda a identificar el módulo más similar.

            MÓDULOS DISPONIBLES:
            - A
            - B

            INPUT DEL USUARIO: "{user_input}"

            INSTRUCCIONES:
            1. Analiza el input del usuario y compáralo con los módulos disponibles
            2. Identifica el módulo que mejor coincida (A o B)
            3. Si no hay coincidencia clara, responde "NO_MATCH"

            RESPONDE SOLO CON "A", "B" O "NO_MATCH":"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error in module identification: {e}")
            return "NO_MATCH"

    async def suggest_category(self, content: str) -> str:
        """Suggests a category based on the provided content."""
        try:
            prompt = f"""Analiza el contenido y sugiere la categoría más apropiada entre: EVALUACIÓN, CLASE, TAREA, SÍLABO, CRONOGRAMA, GENERAL

            CONTENIDO:
            {content}

            RESPONDE SOLO CON LA CATEGORÍA MÁS APROPIADA."""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error in category suggestion: {e}")
            return "GENERAL"

    async def process_query(self, query: str, course_info: str, language: str = "es") -> str:
        """Processes a user query about a course."""
        try:
            prompt = f"""Actúa como un asistente de curso universitario. Tu tarea es responder la consulta del alumno usando la información proporcionada. 

            CONTEXTO:
            {course_info}

            CONSULTA DEL ALUMNO: "{query}"

            INSTRUCCIONES PARA RESPONDER:
            1. Prioriza la información de los resultados de búsqueda semántica
            2. Si la consulta es sobre exámenes o evaluaciones:
               - Busca en la sección "EVALUACIÓN" y organiza la información cronológicamente
               - Incluye fechas, formato, materiales permitidos e instrucciones
            3. Para otros temas:
               - Usa la información más relevante encontrada por la búsqueda semántica
               - Complementa con información adicional si es necesario
            4. Formato:
               - Sé conciso y directo
               - Usa viñetas para cada punto
               - Cita las fuentes
               - Resalta fechas importantes

            RESPONDE AHORA en {'quechua' if language == 'qu' else 'español'}. Traduce incluso la información que has encontrado:"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "Lo siento, hubo un error al procesar tu consulta. Por favor, intenta de nuevo."
