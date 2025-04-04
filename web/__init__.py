from .routes import app
from .models.models import User
from .config.config import MONTH_NAMES

def get_db():
    from .config.config import get_db as _get_db
    return _get_db()