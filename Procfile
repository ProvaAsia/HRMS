web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn hrms.wsgi --log-file - --timeout 120 --workers 2
