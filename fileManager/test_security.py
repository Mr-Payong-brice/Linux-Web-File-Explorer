#!/usr/bin/env python3
"""
Script de test pour valider la sécurité du système de gestion de fichiers
Teste les règles d'isolation utilisateur et les restrictions d'accès
"""

import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import User, AnonymousUser

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fileManager.settings')
django.setup()

from fileManager.middleware import FileSecurityMiddleware
from fileapp.services import get_user_service
from django.conf import settings


def test_security_rules():
    """Tester les règles de sécurité"""
    print("🔐 TEST DES RÈGLES DE SÉCURITÉ")
    print("=" * 50)
    
    factory = RequestFactory()
    middleware = FileSecurityMiddleware(lambda r: None)
    
    # Test 1: Accès à la racine du système (doit être interdit)
    print("\n1️⃣ Test accès à / (racine système):")
    request = factory.get('/', {'path': '/'})
    request.user = User(username='testuser')
    
    response = middleware(request)
    if response.status_code == 403:
        print("✅ ACCÈS À / CORRECTEMENT INTERDIT")
    else:
        print("❌ ÉCHEC: Accès à / non bloqué")
    
    # Test 2: Accès aux répertoires système (doit être interdit)
    print("\n2️⃣ Test accès aux répertoires système:")
    system_paths = ['/etc', '/usr/bin', '/var/log']
    for path in system_paths:
        request = factory.get('/', {'path': path})
        request.user = User(username='testuser')
        response = middleware(request)
        if response.status_code == 403:
            print(f"✅ Accès à {path} correctement interdit")
        else:
            print(f"❌ ÉCHEC: Accès à {path} non bloqué")
    
    # Test 3: Isolation utilisateur
    print("\n3️⃣ Test isolation utilisateur:")
    user1 = User(username='alice')
    user2 = User(username='bob')
    
    # Créer les requêtes pour chaque utilisateur
    request1 = factory.get('/', {'path': '/home/bricevalery/bob'})
    request1.user = user1
    
    request2 = factory.get('/', {'path': '/home/bricevalery/alice'})
    request2.user = user2
    
    # Alice ne doit pas accéder au dossier de Bob
    response1 = middleware(request1)
    if response1.status_code == 403:
        print("✅ Alice ne peut pas accéder au dossier de Bob")
    else:
        print("❌ ÉCHEC: Alice peut accéder au dossier de Bob")
    
    # Bob ne doit pas accéder au dossier d'Alice
    response2 = middleware(request2)
    if response2.status_code == 403:
        print("✅ Bob ne peut pas accéder au dossier d'Alice")
    else:
        print("❌ ÉCHEC: Bob peut accéder au dossier d'Alice")
    
    # Test 4: Accès autorisé dans son propre dossier
    print("\n4️⃣ Test accès autorisé (propre dossier):")
    request = factory.get('/', {'path': '/home/bricevalery/alice'})
    request.user = user1
    
    response = middleware(request)
    if response is None:  # Pas de réponse = middleware laisse passer
        print("✅ Alice peut accéder à son propre dossier")
    else:
        print("❌ ÉCHEC: Alice ne peut pas accéder à son propre dossier")


def test_user_service():
    """Tester le service de gestion des fichiers"""
    print("\n\n📁 TEST DU SERVICE DE FICHIERS")
    print("=" * 50)
    
    # Créer un utilisateur de test
    user = User(username='testuser', is_superuser=False)
    service = get_user_service(user)
    
    print(f"\nUtilisateur: {user.username}")
    print(f"Racine autorisée: {service.base_path}")
    
    # Test 1: Créer un répertoire
    print("\n1️⃣ Test création de répertoire:")
    result = service.create_directory('test_folder')
    if result.get('success'):
        print(f"✅ Répertoire créé: {result['path']}")
    else:
        print(f"❌ ÉCHEC: {result.get('error')}")
    
    # Test 2: Lister le contenu
    print("\n2️⃣ Test listage du contenu:")
    result = service.list_directory()
    if result.get('success'):
        print(f"✅ Contenu listé pour: {result['path']}")
        print(f"   Nombre d'éléments: {len(result['items'])}")
    else:
        print(f"❌ ÉCHEC: {result.get('error')}")
    
    # Test 3: Tentative d'accès hors zone
    print("\n3️⃣ Test accès hors zone (doit échouer):")
    result = service.list_directory('/etc')
    if 'error' in result:
        print(f"✅ Accès hors zone correctement bloqué: {result['error']}")
    else:
        print("❌ ÉCHEC: Accès hors zone non bloqué")


def test_superuser():
    """Tester les privilèges superuser"""
    print("\n\n👑 TEST SUPERUSER")
    print("=" * 50)
    
    superuser = User(username='admin', is_superuser=True)
    service = get_user_service(superuser)
    
    print(f"Superuser: {superuser.username}")
    print(f"Racine autorisée: {service.base_path}")
    
    # Le superuser doit avoir accès à FILE_MANAGER_ROOT complet
    expected_root = settings.FILE_MANAGER_ROOT
    if service.base_path == expected_root:
        print("✅ Superuser a accès à la racine FILE_MANAGER_ROOT")
    else:
        print(f"❌ ÉCHEC: Attendu {expected_root}, obtenu {service.base_path}")


def main():
    """Fonction principale de test"""
    print("🚀 LANCEMENT DES TESTS DE SÉCURITÉ")
    print(f"FILE_MANAGER_ROOT: {settings.FILE_MANAGER_ROOT}")
    print(f"FILE_MANAGER_USER_ISOLATION: {settings.FILE_MANAGER_USER_ISOLATION}")
    
    try:
        test_security_rules()
        test_user_service()
        test_superuser()
        
        print("\n\n🎉 TESTS TERMINÉS")
        print("Vérifiez les résultats ci-dessus pour valider la sécurité")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
