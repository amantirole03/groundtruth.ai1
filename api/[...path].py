import os
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(file_dir)

candidates = [
    os.path.join(parent_dir, "backend"),
    os.path.join(file_dir, "backend"),
    os.path.join(os.getcwd(), "backend"),
    parent_dir,
    file_dir,
    os.getcwd(),
]

for c in candidates:
    if os.path.isdir(c) and c not in sys.path:
        sys.path.insert(0, c)

try:
    from backend.app.main import app
except ImportError:
    from app.main import app

handler = app
