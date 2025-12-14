# conftest.py (en la raíz)
import sys
from pathlib import Path

# Agregar raíz del proyecto al PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))
