"""
WSGI config for core project.
"""
import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application


def _load_env():
    try:
        from dotenv import load_dotenv
        env_file = Path(__file__).resolve().parent.parent / '.env'
        load_dotenv(env_file, override=False)
    except ImportError:
        pass


_load_env()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
application = get_wsgi_application()
