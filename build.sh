#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Automatically create superuser if environment variables exist
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
import os;
username = os.environ.get('DJANGO_SUPERUSER_USERNAME');
email = os.environ.get('DJANGO_SUPERUSER_EMAIL');
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD');
if username and password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password);
    print('Superuser created successfully');
"