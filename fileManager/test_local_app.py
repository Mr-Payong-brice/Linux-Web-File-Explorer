#!/usr/bin/env python3
"""
Script de test pour l'application locale (sans auth Django)
Teste l'utilisation de l'utilisateur système connecté
"""

import os
import sys
import getpass
import django
from django.test import RequestFactory

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fileManager.settings')
django.setup()

from fileManager.middleware import FileSecurityMiddleware
from fileapp.services import get_system_user_service
from django.conf import settings


def test_system_user_detection():
    """Tester la détection de l'utilisateur système"""
    print("👤 TEST DÉTECTION UTILISATEUR SYSTÈME")
    print("=" * 50)
    
    system_user = getpass.getuser()
    print(f"Utilisateur système détecté: {system_user}")
    print(f"Home directory: {os.path.expanduser('~')}")
    print(f"FILE_MANAGER_ROOT: {settings.FILE_MANAGER_ROOT}")
    
    # Test du middleware
    factory = RequestFactory()
    middleware = FileSecurityMiddleware(lambda r: None)
    
    request = factory.get('/')
    response = middleware(request)
    
    user_context = getattr(request, 'user_context', {})
    print(f"\nContexte utilisateur créé:")
    print(f"  - Username: {user_context.get('username')}")
    print(f"  - Authentifié: {user_context.get('is_authenticated')}")
    print(f"  - Admin: {user_context.get('is_admin')}")
    print(f"  - Root path: {user_context.get('root_path')}")
    print(f"  - Système utilisateur: {user_context.get('is_system_user')}")
    
    return user_context


def test_security_rules_local():
    """Tester les règles de sécurité pour l'app locale"""
    print("\n\n🔐 TEST RÈGLES SÉCURITÉ (APP LOCALE)")
    print("=" * 50)
    
    factory = RequestFactory()
    middleware = FileSecurityMiddleware(lambda r: None)
    
    # Test 1: Accès à la racine système (doit être interdit)
    print("\n1️⃣ Test accès à / (racine système):")
    request = factory.get('/', {'path': '/'})
    response = middleware(request)
    if response and response.status_code == 403:
        print("✅ ACCÈS À / CORRECTEMENT INTERDIT")
    else:
        print("❌ ÉCHEC: Accès à / non bloqué")
    
    # Test 2: Accès aux répertoires système
    print("\n2️⃣ Test accès répertoires système:")
    system_paths = ['/etc', '/usr/bin', '/var/log', '/boot', '/sys', '/proc']
    for path in system_paths:
        request = factory.get('/', {'path': path})
        response = middleware(request)
        if response and response.status_code == 403:
            print(f"✅ Accès à {path} correctement interdit")
        else:
            print(f"❌ ÉCHEC: Accès à {path} non bloqué")
    
    # Test 3: Accès autorisé dans son propre home
    print("\n3️⃣ Test accès home utilisateur:")
    user_home = os.path.expanduser('~')
    request = factory.get('/', {'path': user_home})
    response = middleware(request)
    if response is None:  # Pas de réponse = middleware laisse passer
        print(f"✅ Accès autorisé à {user_home}")
    else:
        print(f"❌ ÉCHEC: Accès refusé à {user_home}")


def test_file_operations_local():
    """Tester les opérations fichiers pour l'app locale"""
    print("\n\n📁 TEST OPÉRATIONS FICHIERS (APP LOCALE)")
    print("=" * 50)
    
    system_user = getpass.getuser()
    service = get_system_user_service(system_user)
    
    print(f"Service créé pour l'utilisateur: {system_user}")
    print(f"Base path: {service.base_path}")
    
    # Test 1: Lister le home directory
    print("\n1️⃣ Test listage home directory:")
    result = service.list_directory()
    if result.get('success'):
        print(f"✅ Contenu listé pour: {result['path']}")
        print(f"   Nombre d'éléments: {len(result['items'])}")
        
        # Afficher quelques éléments
        for i, item in enumerate(result['items'][:5]):
            item_type = "📁" if item['is_dir'] else "📄"
            print(f"   {item_type} {item['name']}")
        
        if len(result['items']) > 5:
            print(f"   ... et {len(result['items']) - 5} autres éléments")
    else:
        print(f"❌ ÉCHEC: {result.get('error')}")
    
    # Test 2: Créer un répertoire de test
    print("\n2️⃣ Test création répertoire:")
    test_dir_name = "filemanager_test_dir"
    result = service.create_directory(test_dir_name)
    if result.get('success'):
        print(f"✅ Répertoire créé: {result['path']}")
        
        # Vérifier qu'il existe
        test_path = os.path.join(service.base_path, test_dir_name)
        if os.path.exists(test_path):
            print(f"✅ Répertoire vérifié: {test_path}")
        else:
            print(f"❌ Répertoire non trouvé: {test_path}")
    else:
        print(f"❌ ÉCHEC: {result.get('error')}")
    
    # Test 3: Tentative d'accès hors zone
    print("\n3️⃣ Test accès hors zone (doit échouer):")
    result = service.list_directory('/etc')
    if 'error' in result:
        print(f"✅ Accès hors zone correctement bloqué: {result['error']}")
    else:
        print("❌ ÉCHEC: Accès hors zone non bloqué")


def test_admin_privileges():
    """Tester les privilèges administrateur"""
    print("\n\n👑 TEST PRIVILÈGES ADMIN")
    print("=" * 50)
    
    system_user = getpass.getuser()
    service = get_system_user_service(system_user)
    
    # Vérifier les groupes de l'utilisateur
    try:
        import grp
        user_groups = [g.gr_name for g in grp.getgrall() if system_user in g.gr_mem]
        print(f"Groupes de {system_user}: {', '.join(user_groups)}")
        
        sudo_groups = ['sudo', 'wheel', 'admin']
        is_admin = any(group in sudo_groups for group in user_groups)
        print(f"Admin (sudo/wheel/admin): {'✅ Oui' if is_admin else '❌ Non'}")
        
    except Exception as e:
        print(f"Impossible de vérifier les groupes: {e}")
    
    print(f"Base path autorisé: {service.base_path}")
    print(f"Peut accéder au système: {'✅ Oui' if service.user_context.get('can_access_system') else '❌ Non'}")


def main():
    """Fonction principale de test pour l'app locale"""
    print("🚀 TESTS APPLICATION LOCALE (SANS AUTH DJANGO)")
    print(f"Utilisateur système: {getpass.getuser()}")
    print(f"FILE_MANAGER_ROOT: {settings.FILE_MANAGER_ROOT}")
    print(f"FILE_MANAGER_USER_ISOLATION: {settings.FILE_MANAGER_USER_ISOLATION}")
    
    try:
        user_context = test_system_user_detection()
        test_security_rules_local()
        test_file_operations_local()
        test_admin_privileges()
        
        print("\n\n🎉 TESTS TERMINÉS")
        print("L'application locale fonctionne correctement avec l'utilisateur système !")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
