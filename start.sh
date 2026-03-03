#!/bin/bash
# Script de lancement du File Manager Django

echo "🚀 Lancement du File Manager..."

# Activation du virtualenv
source venv/bin/activate

# Aller dans le dossier du projet Django
cd fileManager/

# Lancer le serveur de développement
python manage.py runserver
