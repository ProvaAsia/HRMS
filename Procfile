web: python manage.py collectstatic --noinput && gunicorn hrms.wsgi --log-file -
release: python manage.py migrate --noinput
