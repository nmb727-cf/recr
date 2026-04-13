#!/usr/bin/env python
import os
import sys
from pathlib import Path


def _load_env():
    """Load .env from the project root (same directory as manage.py)."""
    try:
        from dotenv import load_dotenv
        env_file = Path(__file__).resolve().parent / '.env'
        load_dotenv(env_file, override=False)  # override=False keeps real env vars winning
    except ImportError:
        pass  # python-dotenv not installed — env vars must come from the shell


def main():
    _load_env()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
