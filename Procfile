web: gunicorn chat_project.asgi:application -k uvicorn.workers.UvicornWorker
release: python manage.py migrate
