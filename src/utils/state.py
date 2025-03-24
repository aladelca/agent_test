from typing import Dict
from models.state import State, create_initial_state
from config.settings import logger

class StateManager:
    def __init__(self):
        """Initializes the state manager."""
        self.user_states: Dict[str, State] = {}

    def get_user_state(self, user_id: str) -> State:
        """Gets a user's state, creating it if it doesn't exist."""
        if user_id not in self.user_states:
            self.user_states[user_id] = create_initial_state()
        
        # Clean old messages if there are more than 50
        if len(self.user_states[user_id]["messages"]) > 50:
            self.user_states[user_id]["messages"] = self.user_states[user_id]["messages"][-50:]
        
        return self.user_states[user_id]

    async def reset_state(self, state: State) -> None:
        """Resets the user's state to the main menu."""
        keys_to_reset = [
            "course", "section", "ciclo", "modulo",
            "waiting_for_course", "waiting_for_ciclo", "waiting_for_modulo", "waiting_for_section",
            "pending_course_confirmation", "updating_course", "update_step",
            "update_course", "update_content", "update_category", "update_ciclo", "update_modulo",
            "update_file_path", "temp_file_path"
        ]
        
        for key in keys_to_reset:
            if key in state:
                state[key] = None if key not in ["waiting_for_course", "can_return_to_menu"] else False
        
        state["waiting_for_course"] = True
        state["can_return_to_menu"] = True
        
        logger.debug(f"State reset: {state}")

    def clear_user_state(self, user_id: str) -> None:
        """Deletes a user's state."""
        if user_id in self.user_states:
            del self.user_states[user_id]
            logger.debug(f"State deleted for user: {user_id}")

# Global instance of the state manager
state_manager = StateManager()
