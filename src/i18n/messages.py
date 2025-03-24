from typing import Dict

def get_translated_messages(language: str = "es") -> Dict[str, str]:
    """Returns translated messages based on the selected language."""
    messages = {
        "es": {
            "welcome": "¡Bienvenido al asistente de cursos! 👋\n\n",
            "disclaimer": "\n\n⚠️ Este es un asistente de IA entrenado con datos del curso. Por favor, verifica la información con tus profesores.\nPara cualquier consulta, contacta al profesor Carlos Adrian Alarcon: pciscala@upc.edu.pe",
            "course_selection": "Por favor, selecciona un curso de la lista:\n\n(Escribe 'menu' para volver al menú principal)",
            "ciclo_selection": "Por favor, ingresa el ciclo en formato YYYY1 o YYYY2 (ejemplo: 20241 para el primer semestre de 2024):\n\n(Escribe 'menu' para volver al menú principal)",
            "modulo_selection": "Por favor, selecciona el módulo (A o B):\n\n(Escribe 'menu' para volver al menú principal)",
            "section_selection": "Por favor, ingresa la sección del curso (ejemplo: G1, G2, etc.):\n\n(Escribe 'menu' para volver al menú principal)",
            "ready_for_query": "¡Perfecto! Ahora puedes hacer preguntas sobre el curso.\n\n(Escribe 'menu' para volver al menú principal)",
            "invalid_course": "Por favor, selecciona un curso válido de la lista.\n\n(Escribe 'menu' para volver al menú principal)",
            "invalid_ciclo": "Por favor, ingresa un ciclo válido en formato YYYY1 o YYYY2 (ejemplo: 20241).\n\n(Escribe 'menu' para volver al menú principal)",
            "invalid_modulo": "Por favor, selecciona un módulo válido (A o B).\n\n(Escribe 'menu' para volver al menú principal)",
            "invalid_section": "La sección no puede estar vacía. Por favor, ingresa una sección válida.\n\n(Escribe 'menu' para volver al menú principal)",
            "error_processing": "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.\n\n(Escribe 'menu' para volver al menú principal)",
            "update_usage": "Uso: /update curso;sección;ciclo;módulo;categoría;actualización\n\n(Escribe 'menu' para volver al menú principal)",
            "update_fields": "Por favor, proporciona todos los campos requeridos.\n\n(Escribe 'menu' para volver al menú principal)",
            "update_success": "✅ Actualización guardada correctamente.\n\n(Escribe 'menu' para volver al menú principal)",
            "update_empty": "❌ La actualización no puede estar vacía.\n\n(Escribe 'menu' para volver al menú principal)",
            "update_error": "❌ Error al guardar la actualización: {}\n\n(Escribe 'menu' para volver al menú principal)",
            "course_changed": "✅ Curso cambiado correctamente.\n\n(Escribe 'menu' para volver al menú principal)",
            "please_start": "Por favor, usa el comando /start para comenzar.",
            "complete_info": "Por favor, completa la información del curso usando el comando /start.",
            "return_to_menu": "🔄 Volviendo al menú principal...",
            "no_course_info": "No encontré información para el curso '{}' en el ciclo {} y módulo {}.\n\n(Escribe 'menu' para volver al menú principal)",
            "course_info": """Información del curso:
            Nombre: {}
            Sección: {}
            Ciclo: {}
            Módulo: {}
            Categorías: {}
            Última actualización: {}
            Actualizaciones disponibles: {}
            
            Actualizaciones:
            {}""",
            "course_selected": "✅ Curso seleccionado: {}",
            "update_welcome": "👋 ¡Hola profesor! Bienvenido al sistema de actualización de cursos.",
            "enter_update_content": "Por favor, ingresa el contenido de la actualización o envía el documento que deseas subir.",
            "content_received": "📝 Contenido recibido",
            "suggested_category": "Categoría sugerida: {}",
            "confirm_category": "¿Deseas confirmar esta categoría? (sí/no)",
            "enter_category": "Por favor, ingresa la categoría deseada (EVALUACIÓN, CLASE, TAREA, SÍLABO, CRONOGRAMA, GENERAL):",
            "invalid_category": "❌ Categoría no válida. Por favor, selecciona una de las opciones disponibles.",
            "update_summary": """✅ ¡Actualización guardada exitosamente!

Resumen:
- Curso: {}
- Sección: {}
- Categoría: {}
- Ciclo: {}
- Módulo: {}
- Contenido: {}""",
        },
        "qu": {
            "welcome": "¡Allin hamunayki yachay yanapaqman! 👋\n\n",
            "disclaimer": "\n\n⚠️ Kayqa yachay wasimanta yachachisqa IA yanapakuqmi. Ama hina kaspa, yachachiqkunawan willakuyta chiqaqchay.\nIma tapukuypaqpas, yachachiq Carlos Adrian Alarconwan rimanakuy: pciscala@upc.edu.pe",
            "course_selection": "Ama hina kaspa, huk yachayta akllay kay listamanta:\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "ciclo_selection": "Ama hina kaspa, YYYY1 utaq YYYY2 formatupi cicloykita qillqay (ejemplopaq: 20241 ñawpaq semestrepaq 2024 watapi):\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "modulo_selection": "Ama hina kaspa, akllay huk modulota (A utaq B):\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "section_selection": "Ama hina kaspa, seccionniykita qillqay (ejemplopaq: G1, G2, hukniraq):\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "ready_for_query": "¡Allinmi! Kunanqa yachaymanta tapukuyta atinki.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "invalid_course": "Ama hina kaspa, listamanta allin yachayta akllay.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "invalid_ciclo": "Ama hina kaspa, allin YYYY1 utaq YYYY2 formatupi cicloykita qillqay (ejemplopaq: 20241).\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "invalid_modulo": "Ama hina kaspa, allin modulota akllay (A utaq B).\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "invalid_section": "Seccionniyki mana ch'usaqchu kanan. Ama hina kaspa, allin seccionniykita qillqay.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "error_processing": "Pampachaway, willakuyniykita procesaypi pantay karqan. Ama hina kaspa, huktawan ruwapay.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "update_usage": "Llamk'apay: /update yachay;seccion;ciclo;modulo;categoria;musuqyachiy\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "update_fields": "Ama hina kaspa, tukuy necesario kamachikkunata quy.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "update_success": "✅ Musuqyachiy allinta waqaychasqa.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "update_empty": "❌ Musuqyachiy mana ch'usaqchu kanan atin.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "update_error": "❌ Musuqyachiy waqaychaypi pantay: {}\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "course_changed": "✅ Yachay allinta tikrasqa.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "please_start": "Ama hina kaspa, /start kamachita llamk'achiy qallarinaykipaq.",
            "complete_info": "Ama hina kaspa, /start kamachita llamk'achispa yachaymanta willakuyta hunt'achiy.",
            "return_to_menu": "🔄 Qallariy patamanman kutispa...",
            "no_course_info": "Mana tarinichu willakuyta kay yachaypaq '{}' kay ciclo {} kay modulo {}pi.\n\n(Qillqay 'menu' qallariy patamanman kutirinaykipaq)",
            "course_info": """Yachaymanta willakuy:
            Suti: {}
            Seccion: {}
            Ciclo: {}
            Modulo: {}
            Categorias: {}
            Qhipa musuqyachiy: {}
            Musuqyachiykuna tarisqa: {}
            
            Musuqyachiykuna:
            {}""",
            "course_selected": "✅ Yachay akllasqa: {}",
            "update_welcome": "👋 Allin hamunayki yachachiq! Yachaykuna musuqyachiy sistemaman.",
            "enter_update_content": "Ama hina kaspa, musuqyachiy willakuyta qillqay utaq documentota apachimuy.",
            "content_received": "📝 Willakuy chaskisqa",
            "suggested_category": "Categoria ñisqa: {}",
            "confirm_category": "¿Kay categoriataq allinchu? (arí/mana)",
            "enter_category": "Ama hina kaspa, munasqayki categoriataq qillqay (EVALUACIÓN, CLASE, TAREA, SÍLABO, CRONOGRAMA, GENERAL):",
            "invalid_category": "❌ Mana allin categoria. Ama hina kaspa, huk akllasqa opcionmanta akllay.",
            "update_summary": """✅ ¡Musuqyachiy allinta waqaychasqa!

Tukuy willakuy:
- Yachay: {}
- Seccion: {}
- Categoria: {}
- Ciclo: {}
- Modulo: {}
- Willakuy: {}""",
        }
    }
    return messages.get(language, messages["es"])
