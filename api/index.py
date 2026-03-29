import sys
import os

# Ensure the project root is on the path so src/* imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force SQLite into /tmp before dotenv or any other import can set DB_PATH,
# since Vercel's filesystem is read-only everywhere except /tmp.
os.environ["DB_PATH"] = "/tmp/streamfind.db"

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=False)

from src.db import init_db
init_db()

from src.web_ui import app
