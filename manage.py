# import os
# import subprocess
# import sys
#
#
# def run_celery():
#     subprocess.Popen(
#         ["celery", "-A", "config", "worker", "--loglevel=info", "--pool=gevent"]
#     )
#
#
# def main():
#     BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     sys.path.append(BASE_DIR)
#
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
#
#     try:
#         import django
#
#         django.setup()
#         run_celery()
#
#         from django.core.management import execute_from_command_line
#
#         execute_from_command_line(sys.argv)
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#
#
# if __name__ == "__main__":
#     main()
import os
import subprocess
import sys
from multiprocessing import Process

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Path to the virtual environment
VENV_PATH = os.path.join(BASE_DIR, "venv", "Scripts", "activate")


def run_main_script():
    """Run the main.py script with virtual environment."""
    subprocess.Popen(f"cmd /k {VENV_PATH} && python ./main.py", shell=True)


def run_celery_worker():
    """Start the Celery worker with virtual environment."""
    subprocess.Popen(
        f"cmd /k {VENV_PATH} && celery -A config worker --loglevel=info --pool=gevent",
        shell=True,
    )


def run_django_server():
    """Start the Django development server with virtual environment."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    subprocess.Popen(f"cmd /k {VENV_PATH} && python manage.py runserver", shell=True)


def main():
    """Start all required processes."""
    try:
        # Run Django setup to initialize environment
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        import django

        django.setup()

        # Start processes: main.py, Celery, and the Django server
        processes = []

        # Start the main.py script
        processes.append(Process(target=run_main_script))
        # Start the Celery worker
        processes.append(Process(target=run_celery_worker))
        # Start the Django server
        processes.append(Process(target=run_django_server))

        # Launch all processes
        for process in processes:
            process.start()

        # Wait for processes to complete
        for process in processes:
            process.join()

    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django or required dependencies. "
            "Are you sure everything is installed properly? "
            "Did you forget to activate the virtual environment?"
        ) from exc


if __name__ == "__main__":
    main()
