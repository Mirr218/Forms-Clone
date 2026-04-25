import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Keep tests isolated from project .env and provide required settings.
os.chdir(TESTS_DIR)
os.environ.setdefault("API__TITLE", "Forms API")
os.environ.setdefault("API__DESCRIPTION", "Test API")
os.environ.setdefault("API__VERSION", "1.0.0")
os.environ.setdefault("API__CONTACT_NAME", "Tester")
os.environ.setdefault("API__CONTACT_EMAIL", "tester@example.com")
os.environ.setdefault("API__CONTACT_URL", "https://example.com")
os.environ.setdefault("DATABASE__POSTGRES_HOST", "localhost")
os.environ.setdefault("DATABASE__POSTGRES_PORT", "5432")
os.environ.setdefault("DATABASE__POSTGRES_USER", "postgres")
os.environ.setdefault("DATABASE__POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("DATABASE__POSTGRES_DB", "forms_db")
os.environ.setdefault("SECURITY__JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("SECURITY__JWT_ALGORITHM", "HS256")
os.environ.setdefault("SECURITY__JWT_EXPIRE_MINUTES", "30")
os.environ.setdefault("CORS__ORIGINS", '["http://localhost:3000"]')
