import sys
from pathlib import Path

# Agregar la raíz del proyecto a sys.path para resolución de módulos en tests
sys.path.insert(0, str(Path(__file__).resolve().parent))
