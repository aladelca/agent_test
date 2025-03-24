import os
import boto3
import chardet
from typing import List, Optional
from PyPDF2 import PdfReader
from docx import Document
from unidecode import unidecode
from src.config.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET,
    logger
)
from src.utils.validators import validate_ciclo

class S3Handler:
    def __init__(self):
        """Initializes the S3 handler."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self.bucket = S3_BUCKET

    def _sanitize_path_components(self, course: str, section: str, modulo: str) -> tuple:
        """Sanitizes the path components for S3."""
        course = unidecode(course).replace(" ", "_").lower()
        section = unidecode(section).replace(" ", "_").lower()
        modulo = modulo.upper()
        return course, section, modulo

    async def upload_file(self, file_path: str, course: str, ciclo: str, modulo: str, section: str) -> str:
        """Uploads a file to S3 and returns its URL."""
        try:
            # Validate that all necessary components are present
            if not all([file_path, course, ciclo, modulo, section]):
                missing = []
                if not file_path: missing.append("file")
                if not course: missing.append("course")
                if not ciclo: missing.append("cycle")
                if not modulo: missing.append("module")
                if not section: missing.append("section")
                raise ValueError(f"Missing required path components: {', '.join(missing)}")

            # Validate cycle format
            if not validate_ciclo(ciclo):
                raise ValueError(f"Invalid cycle format: {ciclo}. Must be YYYY1 or YYYY2")

            # Validate module
            if modulo.upper() not in ['A', 'B']:
                raise ValueError(f"Invalid module: {modulo}. Must be A or B")

            # Sanitize folder names
            course, section, modulo = self._sanitize_path_components(course, section, modulo)
            
            # Build S3 path
            s3_path = f"{course}/{ciclo}/{modulo}/{section}/{os.path.basename(file_path)}"
            
            # Ensure file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File {file_path} does not exist")
            
            # Upload file to S3
            self.s3_client.upload_file(file_path, self.bucket, s3_path)
            logger.info(f"File successfully uploaded to s3://{self.bucket}/{s3_path}")
            
            return f"s3://{self.bucket}/{s3_path}"
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise

    async def list_documents(self, course: str, ciclo: str, modulo: str, section: str) -> List[str]:
        """Lists all available documents in a specific S3 path."""
        try:
            # Sanitize folder names
            course, section, modulo = self._sanitize_path_components(course, section, modulo)

            # Validate cycle format
            if not validate_ciclo(ciclo):
                raise ValueError(f"Invalid cycle format: {ciclo}. Must be YYYY1 or YYYY2")

            # Build prefix for search
            prefix = f"{course}/{ciclo}/{modulo}/{section}/"
            
            # List objects in bucket
            logger.info(f"🔍 Searching for documents in path: s3://{self.bucket}/{prefix}")
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )

            # Extract document keys
            documents = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    doc_key = obj['Key']
                    doc_size = obj['Size']
                    doc_modified = obj['LastModified']
                    documents.append(doc_key)
                    logger.info(f"📄 Document: s3://{self.bucket}/{doc_key}")
                    logger.info(f"   - Size: {doc_size/1024:.2f} KB")
                    logger.info(f"   - Last modified: {doc_modified}")

            return documents
        except Exception as e:
            logger.error(f"❌ Error listing documents from S3: {e}")
            return []

    async def get_document_content(self, s3_url: str, course: str, ciclo: str, modulo: str, section: str) -> Optional[str]:
        """Gets the content of a document from S3."""
        try:
            # Validate that all necessary components are present
            if not all([course, ciclo, modulo, section]):
                missing = []
                if not course: missing.append("course")
                if not ciclo: missing.append("cycle")
                if not modulo: missing.append("module")
                if not section: missing.append("section")
                raise ValueError(f"Missing required path components: {', '.join(missing)}")

            # Sanitize folder names
            course, section, modulo = self._sanitize_path_components(course, section, modulo)

            # Extract bucket and key from s3_url
            path_parts = s3_url.replace("s3://", "").split("/")
            bucket = path_parts[0]
            file_name = path_parts[-1]
            
            # If key ends in /, it's a directory
            if file_name == "":
                logger.warning(f"⚠️ Specified path is a directory: {s3_url}")
                return None
            
            # Build complete S3 path
            key = f"{course}/{ciclo}/{modulo}/{section}/{file_name}"
            
            # Create temporary directory if it doesn't exist
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create unique temporary filename
            temp_path = os.path.join(temp_dir, f"temp_{file_name}")
            
            try:
                # Download file
                logger.info(f"Attempting to download file from s3://{bucket}/{key}")
                self.s3_client.download_file(bucket, key, temp_path)
                
                # Determine file type by extension
                file_extension = os.path.splitext(file_name)[1].lower()
                
                if file_extension == '.pdf':
                    # Process PDF file
                    logger.info(f"Processing PDF file: {file_name}")
                    reader = PdfReader(temp_path)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                elif file_extension in ['.doc', '.docx']:
                    # Process Word file
                    logger.info(f"Processing Word file: {file_name}")
                    doc = Document(temp_path)
                    content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                elif file_extension in ['.txt', '.md', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css']:
                    # Process text files with encoding detection
                    logger.info(f"Processing text file: {file_name}")
                    with open(temp_path, 'rb') as file:
                        raw_data = file.read()
                        detected = chardet.detect(raw_data)
                        encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
                        logger.info(f"Detected encoding: {encoding}")
                    with open(temp_path, 'r', encoding=encoding) as file:
                        content = file.read()
                else:
                    logger.warning(f"⚠️ Unsupported file format: {file_extension}")
                    return None
                
                if not content.strip():
                    logger.warning(f"⚠️ Document is empty after processing: {s3_url}")
                    return None
                
                logger.info(f"✅ Document successfully processed: {file_name}")
                return content
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"Temporary file deleted: {temp_path}")
                    
        except Exception as e:
            logger.error(f"Error downloading from S3: {str(e)}", exc_info=True)
            return None

# Global instance of S3 handler
s3_handler = S3Handler()
