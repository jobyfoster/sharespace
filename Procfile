web: python manage.py runserver 0.0.0.0:$PORT
web: gunicorn sharespace.wsgi
web: python manage.py collectstatic --noinput; gunicorn yourapp.wsgi
