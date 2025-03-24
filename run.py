#!/usr/bin/env python3
"""
Script de inicio para el Course Assistant Bot.
Asegura que el directorio src esté en el Python path.
"""

import os
import sys

# Añadir el directorio src al Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.append(src_path)

# Importar y ejecutar el bot
from main import main

if __name__ == '__main__':
    main() 