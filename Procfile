web: python manage.py collectstatic --noinput && gunicorn hrms.wsgi --log-file - --timeout 120 --workers 2
release: python manage.py migrate --noinput
