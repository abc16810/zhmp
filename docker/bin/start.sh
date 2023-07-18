#!/usr/bin/env bash
NAME="wblog" # Name of the application
DJANGODIR=/app/ # Django project directory
USER=root # the user to run as
GROUP=root # the group to run as
NUM_WORKERS=1 # how many worker processes should Gunicorn spawn
LOG_LEVEL=${GUNICORN_LOG_LEVEL:-'debug'}
DJANGO_WSGI_MODULE=config.wsgi # WSGI module name



echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR

export PYTHONPATH=$DJANGODIR:$PYTHONPATH

python manage.py makemigrations && \
  python manage.py migrate && \
  python manage.py collectstatic --noinput
#  python manage.py compress --force && \
# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
--name $NAME \
--workers $NUM_WORKERS \
--user=$USER --group=$GROUP \
--bind 0.0.0.0:8000 \
--log-level=$LOG_LEVEL \
--log-config=logs.ini
--log-file=- \
--worker-class gevent \
--threads 4
