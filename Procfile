web: python manage.py migrate --noinput && python manage.py setup_registry && python manage.py collectstatic --noinput && gunicorn garden_site.wsgi:application
