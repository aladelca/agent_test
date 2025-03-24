from typing import Tuple

def validate_ciclo(ciclo: str) -> bool:
    """Validates that the cycle has the correct format (YYYY1 or YYYY2)."""
    if not ciclo or len(ciclo) != 5:
        return False
    try:
        year = int(ciclo[:4])
        semester = int(ciclo[4])
        return 2000 <= year <= 2100 and semester in [1, 2]
    except ValueError:
        return False

def validate_modulo(modulo: str) -> bool:
    """Validates that the module is A or B."""
    return modulo.upper() in ['A', 'B']

def validate_section(section: str) -> bool:
    """Validates that the section is not empty."""
    return bool(section and section.strip())

def validate_update_fields(fields: dict) -> Tuple[bool, str]:
    """Validates that all required fields for an update are present."""
    required_fields = {
        "curso": fields.get("update_course"),
        "sección": fields.get("section"),
        "ciclo": fields.get("update_ciclo"),
        "módulo": fields.get("update_modulo"),
        "contenido": fields.get("update_content"),
        "categoría": fields.get("update_category")
    }
    
    missing_fields = [field for field, value in required_fields.items() if not value]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, ""
