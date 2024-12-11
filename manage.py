import os
import subprocess
import sys


def run_celery():
    subprocess.Popen(
        ["celery", "-A", "config", "worker", "--loglevel=info", "--pool=gevent"]
    )


def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(BASE_DIR)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        import django

        django.setup()
        run_celery()

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc


if __name__ == "__main__":
    main()

    






    