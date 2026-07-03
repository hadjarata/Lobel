@echo off
REM Serveur Django accessible sur le réseau local (dev uniquement)
python manage.py runserver 0.0.0.0:8000
