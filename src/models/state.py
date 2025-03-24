from typing import Dict, List, TypedDict, Optional

class State(TypedDict):
    """Model representing a user's state in the system."""
    messages: List[Dict[str, str]]
    course: Optional[str]
    section: Optional[str]
    ciclo: Optional[str]
    modulo: Optional[str]
    waiting_for_course: bool
    waiting_for_ciclo: bool
    waiting_for_modulo: bool
    waiting_for_section: bool
    pending_course_confirmation: Optional[str]
    language: Optional[str]
    waiting_for_language: bool
    updating_course: bool
    update_step: Optional[str]
    update_course: Optional[str]
    update_content: Optional[str]
    update_category: Optional[str]
    update_ciclo: Optional[str]
    update_modulo: Optional[str]
    update_file_path: Optional[str]
    temp_file_path: Optional[str]
    can_return_to_menu: bool

def create_initial_state() -> State:
    """Creates an initial state for a new user."""
    return {
        "messages": [],
        "course": None,
        "section": None,
        "ciclo": None,
        "modulo": None,
        "waiting_for_course": False,
        "waiting_for_ciclo": False,
        "waiting_for_modulo": False,
        "waiting_for_section": False,
        "pending_course_confirmation": None,
        "language": None,
        "waiting_for_language": True,
        "updating_course": False,
        "update_step": None,
        "update_course": None,
        "update_content": None,
        "update_category": None,
        "update_ciclo": None,
        "update_modulo": None,
        "update_file_path": None,
        "temp_file_path": None,
        "can_return_to_menu": True
    }
