#!/usr/bin/env python
"""Django loyihasini boshqarish uchun buyruqlar fayli."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django o'rnatilmagan. Terminalda quyidagini bajaring:\n"
            "    pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
