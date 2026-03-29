import sys
import os

# Ensure the project root is on the path so src/* imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Vercel's filesystem is read-only except /tmp — redirect the DB there if no
# explicit DB_PATH has been set via environment variables.
if not os.environ.get("DB_PATH"):
    os.environ["DB_PATH"] = "/tmp/streamfind.db"

from src.db import init_db
init_db()

from src.web_ui import app
