import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from langchain.chat_models import ChatOpenAI
from typing import Dict, List, TypedDict
from database import CourseDatabase
from semantic_search import SemanticSearch
from langchain.schema import HumanMessage
from unidecode import unidecode
import chardet
from PyPDF2 import PdfReader
from docx import Document
from config.settings import (
    TELEGRAM_BOT_TOKEN,
    logger,
    DB_FILE,
    OPENAI_API_KEY
)
from models.state import State
from utils.state import state_manager
from utils.validators import validate_ciclo
from services.content_moderator import ContentModerator
from services.llm_service import LLMService
from i18n.messages import get_translated_messages

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurar la API key de OpenAI
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Inicializar servicios
db = CourseDatabase()
llm_service = LLMService()
content_moderator = ContentModerator()
semantic_search = SemanticSearch()

# Si existe el archivo JSON, migrar los datos
if os.path.exists(DB_FILE):
    db.migrate_from_json_file(DB_FILE)

# Configuración de S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
S3_BUCKET = os.getenv('S3_BUCKET_NAME')

# Inicializa la LLM
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

def format_updates(updates: List[Dict[str, str]]) -> str:
    """Formatea las actualizaciones para mostrarlas en el mensaje"""
    if not updates:
        return "No hay actualizaciones disponibles."
    
    formatted_updates = []
    for update in updates:
        formatted_updates.append(
            f"- {update['category']} ({update['timestamp']}):\n  {update['content']}"
        )
    return "\n".join(formatted_updates)

def get_translated_messages(language: str = "es") -> Dict[str, str]:
    """Retorna los mensajes traducidos según el idioma seleccionado"""
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

def validate_ciclo(ciclo: str) -> bool:
    """Valida que el ciclo tenga el formato correcto (YYYY1 o YYYY2)."""
    if not ciclo or len(ciclo) != 5:
        return False
    try:
        year = int(ciclo[:4])
        semester = int(ciclo[4])
        return 2000 <= year <= 2100 and semester in [1, 2]
    except ValueError:
        return False

async def upload_to_s3(file_path: str, course: str, ciclo: str, modulo: str, section: str) -> str:
    """Sube un archivo a S3 y retorna su URL.
    
    La estructura de carpetas será:
    bucket/
        curso/
            ciclo/
                modulo/
                    seccion/
                        archivo
    """
    try:
        # Validar que todos los componentes necesarios estén presentes
        if not all([file_path, course, ciclo, modulo, section]):
            missing = []
            if not file_path: missing.append("archivo")
            if not course: missing.append("curso")
            if not ciclo: missing.append("ciclo")
            if not modulo: missing.append("módulo")
            if not section: missing.append("sección")
            raise ValueError(f"Faltan componentes necesarios para la ruta: {', '.join(missing)}")

        # Validar el formato del ciclo
        if not validate_ciclo(ciclo):
            raise ValueError(f"Formato de ciclo inválido: {ciclo}. Debe ser YYYY1 o YYYY2")

        # Validar el módulo
        if modulo.upper() not in ['A', 'B']:
            raise ValueError(f"Módulo inválido: {modulo}. Debe ser A o B")

        # Sanitizar nombres de carpetas para evitar problemas con caracteres especiales
        course = unidecode(course).replace(" ", "_").lower()
        section = unidecode(section).replace(" ", "_").lower()
        modulo = modulo.upper()
        
        # Construir la ruta en S3 siguiendo la estructura estándar
        s3_path = f"{course}/{ciclo}/{modulo}/{section}/{os.path.basename(file_path)}"
        
        # Asegurarse de que el archivo existe
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe")
        
        # Subir el archivo a S3
        s3_client.upload_file(file_path, S3_BUCKET, s3_path)
        logger.info(f"Archivo subido exitosamente a s3://{S3_BUCKET}/{s3_path}")
        
        return f"s3://{S3_BUCKET}/{s3_path}"
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        raise

async def list_s3_documents(course: str, ciclo: str, modulo: str, section: str) -> List[str]:
    """Lista todos los documentos disponibles en una ruta específica de S3"""
    try:
        # Sanitizar nombres de carpetas
        course = unidecode(course).replace(" ", "_").lower()
        section = unidecode(section).replace(" ", "_").lower()
        modulo = modulo.upper()

        # Validar el formato del ciclo
        if not validate_ciclo(ciclo):
            raise ValueError(f"Formato de ciclo inválido: {ciclo}. Debe ser YYYY1 o YYYY2")

        # Validar el módulo
        if modulo not in ['A', 'B']:
            raise ValueError(f"Módulo inválido: {modulo}. Debe ser A o B")

        # Construir el prefijo para la búsqueda
        prefix = f"{course}/{ciclo}/{modulo}/{section}/"
        
        # Listar objetos en el bucket con el prefijo especificado
        logger.info(f"🔍 Buscando documentos en ruta: s3://{S3_BUCKET}/{prefix}")
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix
        )

        # Extraer las keys de los documentos
        documents = []
        if 'Contents' in response:
            logger.info(f"📚 Documentos encontrados en S3:")
            for obj in response['Contents']:
                doc_key = obj['Key']
                doc_size = obj['Size']
                doc_modified = obj['LastModified']
                documents.append(doc_key)
                logger.info(f"📄 Documento: s3://{S3_BUCKET}/{doc_key}")
                logger.info(f"   - Tamaño: {doc_size/1024:.2f} KB")
                logger.info(f"   - Última modificación: {doc_modified}")
        else:
            logger.info(f"❌ No se encontraron documentos en la ruta s3://{S3_BUCKET}/{prefix}")

        return documents
    except Exception as e:
        logger.error(f"❌ Error listando documentos de S3: {e}")
        return []

async def get_document_from_s3(s3_url: str, course: str, ciclo: str, modulo: str, section: str) -> str:
    """Obtiene el contenido de un documento desde S3 siguiendo la estructura de carpetas:
    bucket/curso/ciclo/modulo/seccion/archivo"""
    try:
        # Validar que todos los componentes necesarios estén presentes
        if not all([course, ciclo, modulo, section]):
            missing = []
            if not course: missing.append("curso")
            if not ciclo: missing.append("ciclo")
            if not modulo: missing.append("módulo")
            if not section: missing.append("sección")
            raise ValueError(f"Faltan componentes necesarios para la ruta: {', '.join(missing)}")

        # Sanitizar nombres de carpetas
        course = unidecode(course).replace(" ", "_").lower()
        section = unidecode(section).replace(" ", "_").lower()
        modulo = modulo.upper()

        # Validar el formato del ciclo
        if not validate_ciclo(ciclo):
            raise ValueError(f"Formato de ciclo inválido: {ciclo}. Debe ser YYYY1 o YYYY2")

        # Validar el módulo
        if modulo not in ['A', 'B']:
            raise ValueError(f"Módulo inválido: {modulo}. Debe ser A o B")

        # Extraer bucket y key del s3_url
        path_parts = s3_url.replace("s3://", "").split("/")
        bucket = path_parts[0]
        file_name = path_parts[-1]
        
        # Si la key termina en /, es un directorio, no un archivo
        if file_name == "":
            logger.warning(f"⚠️ La ruta especificada es un directorio, no un archivo: {s3_url}")
            return ""
        
        # Construir la ruta completa en S3
        key = f"{course}/{ciclo}/{modulo}/{section}/{file_name}"
        
        # Crear directorio temporal si no existe
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Crear un nombre de archivo temporal único
        temp_path = os.path.join(temp_dir, f"temp_{file_name}")
        
        try:
            # Descargar el archivo
            logger.info(f"Intentando descargar archivo de s3://{bucket}/{key}")
            s3_client.download_file(bucket, key, temp_path)
            
            # Determinar el tipo de archivo por su extensión
            file_extension = os.path.splitext(file_name)[1].lower()
            
            if file_extension == '.pdf':
                # Procesar archivo PDF
                logger.info(f"Procesando archivo PDF: {file_name}")
                reader = PdfReader(temp_path)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n"
            elif file_extension in ['.doc', '.docx']:
                # Procesar archivo Word
                logger.info(f"Procesando archivo Word: {file_name}")
                doc = Document(temp_path)
                content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            elif file_extension in ['.txt', '.md', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css']:
                # Procesar archivos de texto con detección de codificación
                logger.info(f"Procesando archivo de texto: {file_name}")
                with open(temp_path, 'rb') as file:
                    raw_data = file.read()
                    detected = chardet.detect(raw_data)
                    encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
                    logger.info(f"Codificación detectada: {encoding}")
                with open(temp_path, 'r', encoding=encoding) as file:
                    content = file.read()
            else:
                logger.warning(f"⚠️ Formato de archivo no soportado: {file_extension}")
                return ""
            
            if not content.strip():
                logger.warning(f"⚠️ El documento está vacío después de procesar: {s3_url}")
                return ""
            
            logger.info(f"✅ Documento procesado exitosamente: {file_name}")
            return content
            
        finally:
            # Limpiar el archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Archivo temporal eliminado: {temp_path}")
                
    except Exception as e:
        logger.error(f"Error downloading from S3: {str(e)}", exc_info=True)
        return ""

async def process_query(state: State) -> State:
    """Procesa la consulta del usuario usando la LLM"""
    try:
        last_message = state["messages"][-1]
        consulta = last_message.get("content", "") if isinstance(last_message, dict) else last_message.content

        # Obtener el idioma del usuario
        language = state.get("language", "es")
        messages = get_translated_messages(language)

        # Obtener información del curso de la base de datos
        course_name = state.get("course")
        if not course_name:
            state["messages"].append({"role": "assistant", "content": messages["please_start"]})
            return state

        # Verificar que tenga ciclo, módulo y sección
        if not state.get("ciclo") or not state.get("modulo") or not state.get("section"):
            state["messages"].append({"role": "assistant", "content": messages["complete_info"]})
            return state

        course_info = db.get_course_info(course_name)
        print(course_info)
        if not course_info:
            available_courses = list(db.get_courses().keys())
            courses_text = "\nCursos disponibles:\n- " + "\n- ".join(available_courses) if available_courses else "\nNo hay cursos disponibles en la base de datos."
            state["messages"].append({"role": "assistant", "content": messages["no_course_info"].format(course_name, state['ciclo'], state['modulo']) + courses_text})
            return state

        # Filtrar actualizaciones y documentos por ciclo, módulo y sección
        filtered_updates = [
            update for update in course_info['updates']
            if update.get('ciclo') == state['ciclo'] and 
               update.get('modulo') == state['modulo']
        ]

        filtered_documents = [
            doc for doc in course_info['documents']
            if doc.get('ciclo') == state['ciclo'] and 
               doc.get('modulo') == state['modulo']
        ]

        # Realizar búsqueda semántica
        semantic_search.clear()  # Limpiar índice anterior
        
        # Preparar textos y metadatos para la búsqueda semántica
        texts = []
        metadata = []
        
        # Agregar actualizaciones al índice
        for update in filtered_updates:
            texts.append(update['content'])
            metadata.append({
                'type': 'update',
                'category': update['category'],
                'timestamp': update['timestamp']
            })
        
        # Buscar documentos adicionales en S3
        try:
            logger.info(f"🔄 Iniciando búsqueda de documentos en S3 para:")
            logger.info(f"   - Curso: {state['course']}")
            logger.info(f"   - Ciclo: {state['ciclo']}")
            logger.info(f"   - Módulo: {state['modulo']}")
            logger.info(f"   - Sección: {state['section']}")
            
            s3_documents = await list_s3_documents(
                state['course'],
                state['ciclo'],
                state['modulo'],
                state['section']
            )
            
            # Agregar documentos encontrados en S3 al índice
            if s3_documents:
                logger.info(f"✅ Se encontraron {len(s3_documents)} documentos en S3")
                for doc_key in s3_documents:
                    try:
                        s3_url = f"s3://{S3_BUCKET}/{doc_key}"
                        logger.info(f"📝 Procesando documento: {s3_url}")
                        content = await get_document_from_s3(
                            s3_url,
                            state['course'],
                            state['ciclo'],
                            state['modulo'],
                            state['section']
                        )
                        if content:
                            texts.append(content)
                            metadata.append({
                                'type': 'document',
                                'title': os.path.basename(doc_key),
                                'category': 'S3_DOCUMENT',
                                'source': s3_url
                            })
                            logger.info(f"✅ Documento procesado exitosamente: {os.path.basename(doc_key)}")
                        else:
                            logger.warning(f"⚠️ El documento está vacío: {s3_url}")
                    except Exception as e:
                        logger.error(f"❌ Error procesando documento {doc_key}: {str(e)}")
            else:
                logger.info("ℹ️ No se encontraron documentos en S3")

        except Exception as e:
            logger.error(f"❌ Error en la búsqueda de documentos en S3: {str(e)}")
        
        # Agregar documentos registrados en la base de datos
        for doc in filtered_documents:
            try:
                if doc.get('file_path', '').startswith('s3://'):
                    content = await get_document_from_s3(
                        doc['file_path'],
                        state['course'],
                        state['ciclo'],
                        state['modulo'],
                        state['section']
                    )
                    if content:
                        texts.append(content)
                        metadata.append({
                            'type': 'document',
                            'title': doc['title'],
                            'category': doc['category']
                        })
                        logger.info(f"Documento de base de datos añadido al índice: {doc['title']}")
            except Exception as e:
                logger.error(f"Error procesando documento {doc['title']}: {e}")

        # Indexar los textos si hay contenido
        if texts:
            semantic_search.add_texts(texts, metadata)
            
            # Realizar búsqueda semántica
            search_results = semantic_search.search(consulta, k=5)
            
            # Formatear resultados de búsqueda
            relevant_info = "\n\nInformación más relevante encontrada:\n"
            for text, meta, score in search_results:
                if score > 0.5:  # Solo incluir resultados con score mayor a 0.5
                    source_type = "Actualización" if meta['type'] == 'update' else "Documento"
                    category = meta.get('category', 'N/A')
                    timestamp = meta.get('timestamp', '')
                    title = meta.get('title', '')
                    
                    relevant_info += f"\n- {source_type} ({category})"
                    if timestamp:
                        relevant_info += f" del {timestamp}"
                    if title:
                        relevant_info += f" - {title}"
                    relevant_info += f":\n  {text[:200]}..."
        else:
            relevant_info = "\n\nNo se encontró información relevante."

        # Formatear la información del curso
        info_curso = messages["course_info"].format(
            course_info['name'],
            course_info['section'],
            state['ciclo'],
            state['modulo'],
            ', '.join(course_info['categories']),
            course_info['last_update'],
            len(filtered_updates),
            format_updates(filtered_updates)
        )

        # Agregar resultados de búsqueda semántica
        info_curso += relevant_info

        # Obtener el idioma del usuario
        if state.get("language") == "qu":
            language_response = "quechua" 
        else:
            language_response = "español"

        prompt = f"""Actúa como un asistente de curso universitario. Tu tarea es responder la consulta del alumno usando la información proporcionada. 

        CONTEXTO:
        {info_curso}

        CONSULTA DEL ALUMNO: "{consulta}"

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

        RESPONDE AHORA en {language_response}. Traduce incluso la información que has encontrado:"""
        print(prompt)
        response = llm.invoke([HumanMessage(content=prompt)])
        state["messages"].append({"role": "assistant", "content": response.content})
        return state
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        state["messages"].append({
            "role": "assistant", 
            "content": f"Lo siento, hubo un error al procesar tu consulta. Por favor, intenta de nuevo."
        })
        return state

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia la conversación y muestra el menú de selección de idioma"""
    user_id = str(update.effective_user.id)
    state = state_manager.get_user_state(user_id)
    
    if not state.get("language"):
        keyboard = [
            [InlineKeyboardButton("Español 🇵🇪", callback_data="es"),
             InlineKeyboardButton("Quechua 🇵🇪", callback_data="qu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Selecciona tu idioma / Simiykita akllay:",
            reply_markup=reply_markup
        )
        return

    messages = get_translated_messages(state.get("language"))
    available_courses = list(db.get_courses().keys())
    
    if state.get("language") == "qu":
        courses_text = "\nKay yachaykuna kan:\n- " + "\n- ".join(available_courses) if available_courses else "\nMana yachaykuna kanchu base de datospi."
    else:
        courses_text = "\nCursos disponibles:\n- " + "\n- ".join(available_courses) if available_courses else "\nNo hay cursos disponibles en la base de datos."
    
    response = messages["welcome"] + courses_text + messages["disclaimer"]
    await update.message.reply_text(response)
    
    state["waiting_for_course"] = True
    state["can_return_to_menu"] = True

async def update_course_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    state = state_manager.get_user_state(user_id)
    messages = get_translated_messages(state.get("language", "es"))
    
    # Iniciar el flujo de actualización
    state["updating_course"] = True
    state["update_step"] = "course_selection"
    
    available_courses = list(db.get_courses().keys())
    courses_text = "\nCursos disponibles:\n- " + "\n- ".join(available_courses) if available_courses else "\nNo hay cursos disponibles en la base de datos."
    
    await update.message.reply_text(
        f"{messages['update_welcome']}\n\n"
        f"{messages['course_selection']}{courses_text}"
    )

async def handle_update_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    state = state_manager.get_user_state(user_id)
    message = update.message.text if update.message else None
    messages = get_translated_messages(state.get("language", "es"))
    
    if not state.get("updating_course"):
        return
    
    # Verificar si el usuario quiere volver al menú principal
    if message and message.lower() in ['menu', '/menu']:
        await state_manager.reset_state(state)
        available_courses = list(db.get_courses().keys())
        courses_text = "\nCursos disponibles:\n- " + "\n- ".join(available_courses) if available_courses else "\nNo hay cursos disponibles en la base de datos."
        await update.message.reply_text(
            f"{messages['return_to_menu']}\n{messages['welcome']}{courses_text}{messages['disclaimer']}",
            parse_mode='Markdown'
        )
        return
    
    try:
        if state["update_step"] == "course_selection":
            matching_course = await llm_service.identify_course(message, list(db.get_courses().keys()))

            if matching_course != "NO_MATCH":
                state["update_course"] = matching_course
                state["update_step"] = "content_input"
                await update.message.reply_text(
                    f"{messages['course_selected'].format(matching_course)}\n\n"
                    f"{messages['enter_update_content']}\n\n"
                    f"({messages['return_to_menu']})"
                )
            else:
                await update.message.reply_text(messages["invalid_course"])

        elif state["update_step"] == "content_input":
            if not message or not message.strip():
                await update.message.reply_text(messages["update_empty"])
                return
            
            # Verificar que el contenido no sea inapropiado
            is_appropriate, warning = await content_moderator.detect_inappropriate_content(message)
            if not is_appropriate:
                logger.warning(f"Contenido inapropiado detectado en actualización - Usuario: {user_id}, Mensaje: {message}")
                await update.message.reply_text(warning)
                return
            
            state["update_content"] = message.strip()
            suggested_category = await llm_service.suggest_category(message)
            state["update_category"] = suggested_category
            
            await update.message.reply_text(
                f"{messages['content_received']}\n\n"
                f"{messages['suggested_category'].format(suggested_category)}\n\n"
                f"{messages['confirm_category']}\n\n"
                f"({messages['return_to_menu']})"
            )
            state["update_step"] = "category_confirmation"

        elif state["update_step"] == "category_confirmation":
            if message.lower() in ['sí', 'si', 'yes', 'y', 'arí', 'ari']:
                state["update_step"] = "ciclo_selection"
                await update.message.reply_text(messages["ciclo_selection"])
            else:
                state["update_step"] = "category_input"
                await update.message.reply_text(
                    f"{messages['enter_category']}\n\n"
                    f"({messages['return_to_menu']})"
                )

        elif state["update_step"] == "category_input":
            if message.upper() in ['EVALUACIÓN', 'CLASE', 'TAREA', 'SÍLABO', 'CRONOGRAMA', 'GENERAL']:
                state["update_category"] = message.upper()
                state["update_step"] = "ciclo_selection"
                await update.message.reply_text(messages["ciclo_selection"])
            else:
                await update.message.reply_text(messages["invalid_category"])

        elif state["update_step"] == "ciclo_selection":
            if validate_ciclo(message):
                state["update_ciclo"] = message
                state["update_step"] = "section_selection"
                await update.message.reply_text(messages["section_selection"])
            else:
                await update.message.reply_text(messages["invalid_ciclo"])

        elif state["update_step"] == "section_selection":
            if message and message.strip():
                state["section"] = message.strip()
                state["update_step"] = "modulo_selection"
                await update.message.reply_text(messages["modulo_selection"])
            else:
                await update.message.reply_text(messages["invalid_section"])
            return

        elif state["update_step"] == "modulo_selection":
            matching_modulo = await llm_service.identify_module(message)
            if matching_modulo != "NO_MATCH":
                state["update_modulo"] = matching_modulo
                
                try:
                    # Validar que todos los componentes necesarios estén presentes
                    required_fields = {
                        "curso": state.get("update_course"),
                        "sección": state.get("section"),
                        "ciclo": state.get("update_ciclo"),
                        "módulo": state.get("update_modulo"),
                        "contenido": state.get("update_content"),
                        "categoría": state.get("update_category")
                    }
                    
                    missing_fields = [field for field, value in required_fields.items() if not value]
                    if missing_fields:
                        raise ValueError(f"Faltan campos requeridos: {', '.join(missing_fields)}")

                    # Guardar la actualización en la base de datos
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Obtener el ID del curso
                        cursor.execute("SELECT id FROM courses WHERE name = ?", (state["update_course"],))
                        course_id = cursor.fetchone()[0]
                        
                        # Insertar la actualización
                        cursor.execute("""
                            INSERT INTO updates (course_id, content, category, ciclo, modulo, section)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            course_id,
                            state["update_content"],
                            state["update_category"],
                            state["update_ciclo"],
                            state["update_modulo"],
                            state["section"]
                        ))
                        
                        conn.commit()
                    
                    # Preparar resumen
                    update_summary = {
                        "course": state["update_course"],
                        "section": state["section"],
                        "category": state["update_category"],
                        "ciclo": state["update_ciclo"],
                        "modulo": state["update_modulo"],
                        "content": state["update_content"][:100] + "..." if len(state["update_content"]) > 100 else state["update_content"]
                    }
                    
                    # Limpiar el estado de actualización
                    await state_manager.reset_state(state)
                    
                    await update.message.reply_text(
                        messages["update_summary"].format(
                            update_summary['course'],
                            update_summary['section'],
                            update_summary['category'],
                            update_summary['ciclo'],
                            update_summary['modulo'],
                            update_summary['content']
                        ) + f"\n\n({messages['return_to_menu']})"
                    )
                            
                except Exception as e:
                    logger.error(f"Error al guardar la actualización: {str(e)}")
                    await update.message.reply_text(messages["update_error"].format(str(e)))
            else:
                await update.message.reply_text(messages["invalid_modulo"])

    except Exception as e:
        logger.error(f"Error en handle_update_flow: {str(e)}")
        await update.message.reply_text(messages["error_processing"])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes recibidos"""
    try:
        user_id = str(update.effective_user.id)
        message = update.message.text if update.message else None
        state = state_manager.get_user_state(user_id)
        messages = get_translated_messages(state.get("language", "es"))

        # Verificar si el usuario quiere volver al menú principal
        if message and message.lower() in ['menu', '/menu'] and state.get("can_return_to_menu"):
            await state_manager.reset_state(state)
            available_courses = list(db.get_courses().keys())
            courses_text = "\nCursos disponibles:\n- " + "\n- ".join(available_courses) if available_courses else "\nNo hay cursos disponibles en la base de datos."
            await update.message.reply_text(
                f"{messages['return_to_menu']}\n{messages['welcome']}{courses_text}{messages['disclaimer']}",
                parse_mode='Markdown'
            )
            return

        # Si hay mensaje, verificar que no sea inapropiado
        if message:
            is_appropriate, warning = await content_moderator.detect_inappropriate_content(message)
            if not is_appropriate:
                logger.warning(f"Contenido inapropiado detectado - Usuario: {user_id}, Mensaje: {message}")
                await update.message.reply_text(warning)
                return

        # Verificar si está en proceso de actualización
        if state.get("updating_course"):
            await handle_update_flow(update, context)
            return

        # Manejar selección de idioma
        if state.get("waiting_for_language"):
            if message in ['1', 'es', 'español', 'spanish']:
                state["language"] = "es"
                state["waiting_for_language"] = False
                available_courses = list(db.get_courses().keys())
                courses_text = "\nCursos disponibles:\n- " + "\n- ".join(available_courses) if available_courses else "\nNo hay cursos disponibles en la base de datos."
                await update.message.reply_text(
                    f"{messages['welcome']}{courses_text}{messages['disclaimer']}",
                    parse_mode='Markdown'
                )
                state["waiting_for_course"] = True
            elif message in ['2', 'qu', 'quechua', 'qichwa']:
                state["language"] = "qu"
                state["waiting_for_language"] = False
                available_courses = list(db.get_courses().keys())
                courses_text = "\nKay yachaykuna kan:\n- " + "\n- ".join(available_courses) if available_courses else "\nMana yachaykuna kanchu base de datospi."
                await update.message.reply_text(
                    f"{messages['welcome']}{courses_text}{messages['disclaimer']}",
                    parse_mode='Markdown'
                )
                state["waiting_for_course"] = True
            else:
                await update.message.reply_text("Por favor, selecciona un idioma válido (1/2)")
            return

        # Manejar selección de curso
        if state.get("waiting_for_course"):
            if message:
                available_courses = list(db.get_courses().keys())
                logger.info(f"Buscando curso para entrada: '{message}' entre cursos disponibles: {available_courses}")
                
                matching_course = await llm_service.identify_course(message, available_courses)
                
                if matching_course != "NO_MATCH":
                    state["course"] = matching_course
                    state["waiting_for_course"] = False
                    state["waiting_for_section"] = True
                    await update.message.reply_text(
                        f"{messages['course_selected'].format(matching_course)}\n\n"
                        f"{messages['section_selection']}"
                    )
                else:
                    suggestions = "\n".join([f"- {course}" for course in available_courses])
                    await update.message.reply_text(
                        f"❌ No pude encontrar el curso '{message}'.\n\n"
                        f"Cursos disponibles:\n{suggestions}\n\n"
                        "Por favor, intenta escribir el nombre exacto de uno de estos cursos."
                    )
                return

        # Manejar selección de sección
        if state.get("waiting_for_section"):
            if message and message.strip():
                state["section"] = message.strip()
                state["waiting_for_section"] = False
                state["waiting_for_ciclo"] = True
                await update.message.reply_text(messages["ciclo_selection"])
            else:
                await update.message.reply_text(messages["invalid_section"])
            return

        # Manejar selección de ciclo
        if state.get("waiting_for_ciclo"):
            if message:
                if validate_ciclo(message):
                    state["ciclo"] = message
                    state["waiting_for_ciclo"] = False
                    state["waiting_for_modulo"] = True
                    await update.message.reply_text(messages["modulo_selection"])
                else:
                    await update.message.reply_text(messages["invalid_ciclo"])
            return

        # Manejar selección de módulo
        if state.get("waiting_for_modulo"):
            if message:
                matching_modulo = await llm_service.identify_module(message)
                if matching_modulo != "NO_MATCH":
                    state["modulo"] = matching_modulo
                    state["waiting_for_modulo"] = False
                    await update.message.reply_text(messages["ready_for_query"])
                else:
                    await update.message.reply_text(messages["invalid_modulo"])
            return

        # Procesar documento si está presente
        if update.message and update.message.document:
            await update.message.reply_text(
                "❌ Lo siento, la subida de documentos no está disponible en este momento.\n"
                "Por favor, contacta al administrador del curso para subir documentos."
            )
            return

        # Procesar consulta normal
        if message and state.get("course"):
            course_info = db.get_course_info(
                state["course"],
                state["ciclo"],
                state["modulo"],
                state["section"]
            )
            print(course_info)
            if course_info:
                response = await llm_service.process_query(message, course_info, state.get("language", "es"))
                await update.message.reply_text(response)
            else:
                await update.message.reply_text(
                    messages["no_course_info"].format(
                        state["course"],
                        state["ciclo"],
                        state["modulo"]
                    )
                )

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        messages = get_translated_messages(state.get("language", "es"))
        await update.message.reply_text(messages["error_processing"])

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja la selección de idioma mediante botones"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    state = state_manager.get_user_state(user_id)
    
    # Actualizar el idioma seleccionado
    state["language"] = query.data
    state["waiting_for_language"] = False
    
    messages = get_translated_messages(state["language"])
    available_courses = list(db.get_courses().keys())
    
    if state["language"] == "qu":
        courses_text = "\nKay yachaykuna kan:\n- " + "\n- ".join(available_courses) if available_courses else "\nMana yachaykuna kanchu base de datospi."
    else:
        courses_text = "\nCursos disponibles:\n- " + "\n- ".join(available_courses) if available_courses else "\nNo hay cursos disponibles en la base de datos."
    
    response = messages["welcome"] + courses_text + messages["disclaimer"]
    await query.edit_message_text(response)
    
    state["waiting_for_course"] = True
    state["can_return_to_menu"] = True

async def detect_inappropriate_content(message: str) -> tuple[bool, str]:
    """Detecta si un mensaje contiene contenido inapropiado (discriminación, odio, etc.)"""
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

        response = llm.invoke([HumanMessage(content=prompt)])
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
        return True, ""  # En caso de error, permitir el mensaje pero registrar el error

def main() -> None:
    """Inicia el bot"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Añadir manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("update", update_course_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(language_callback))

    # Iniciar el bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error en la aplicación: {e}", exc_info=True)