import os

from .celery import app as celery_app

__all__ = ("celery_app",)

if not os.path.exists(os.path.join(os.path.curdir, "log")):
    os.mkdir(os.path.join(os.path.curdir, "log"))
if not os.path.exists(os.path.join(os.path.curdir, "media")):
    os.mkdir(os.path.join(os.path.curdir, "media"))
