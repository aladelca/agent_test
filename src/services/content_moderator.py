from typing import Tuple
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from src.config.settings import logger, LLM_MODEL, LLM_TEMPERATURE

class ContentModerator:
    def __init__(self):
        """Initializes the content moderator with the LLM model."""
        self.llm = ChatOpenAI(model_name=LLM_MODEL, temperature=LLM_TEMPERATURE)

    async def detect_inappropriate_content(self, message: str) -> Tuple[bool, str]:
        """Detects if a message contains inappropriate content (discrimination, hate speech, etc.)"""
        try:
            prompt = f"""Actúa como un moderador de contenido que detecta mensajes inapropiados.

            MENSAJE A ANALIZAR: "{message}"

            INSTRUCCIONES:
            1. Analiza si el mensaje contiene:
               - Discriminación (racial, género, orientación sexual, religión, etc.)
               - Discurso de odio
               - Acoso o bullying
               - Amenazas
               - Contenido ofensivo o inapropiado
            2. Si detectas alguno de estos elementos:
               - Responde con "INAPPROPRIATE: [tipo de contenido detectado]"
               - Ejemplo: "INAPPROPRIATE: discriminación racial"
            3. Si el mensaje es apropiado:
               - Responde con "APPROPRIATE"

            RESPONDE SOLO CON "APPROPRIATE" O "INAPPROPRIATE: [razón]":"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content.strip()
            
            if result.startswith("INAPPROPRIATE"):
                reason = result.split(":", 1)[1].strip()
                warning_message = (
                    "⚠️ ADVERTENCIA: Tu mensaje ha sido detectado como inapropiado.\n\n"
                    f"Razón: {reason}\n\n"
                    "🚫 Este tipo de contenido está estrictamente prohibido y será reportado "
                    "inmediatamente a las autoridades universitarias.\n\n"
                    "⚠️ Consecuencias:\n"
                    "- Reporte inmediato a la universidad\n"
                    "- Posible expulsión del curso\n"
                    "- Proceso disciplinario\n\n"
                    "Por favor, mantén un ambiente respetuoso y profesional en todas tus interacciones."
                )
                return False, warning_message
            return True, ""
            
        except Exception as e:
            logger.error(f"Error detecting inappropriate content: {e}")
            return True, ""  # In case of error, allow the message but log the error
