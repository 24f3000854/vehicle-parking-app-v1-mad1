import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app

application = app

if __name__ == "__main__":
    app.run()
