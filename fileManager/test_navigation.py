#!/usr/bin/env python3
"""
Script de test pour la navigation dynamique dans les dossiers
Teste les fonctionnalités AJAX et de navigation sans rechargement
"""

import os
import sys
import django
from django.test import RequestFactory, Client
from django.contrib.auth.models import AnonymousUser

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fileManager.settings')
django.setup()

from fileapp.views import home_view
from fileapp.services import get_system_user_service
from django.conf import settings


def test_ajax_navigation():
    """Tester la navigation AJAX"""
    print("🌐 TEST NAVIGATION AJAX")
    print("=" * 50)
    
    # Créer un client de test
    client = Client()
    
    # Simuler une requête normale (page complète)
    print("\n1️⃣ Test requête normale:")
    response = client.get('/')
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type')}")
    
    # Vérifier que la réponse contient le template complet
    if b'base.html' in response.content:
        print("✅ Réponse normale contient base.html")
    else:
        print("❌ Réponse normale ne contient pas base.html")
    
    # Simuler une requête AJAX
    print("\n2️⃣ Test requête AJAX:")
    response = client.get('/', {'ajax': '1'})
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type')}")
    
    # Vérifier que la réponse AJAX ne contient pas base.html
    if b'base.html' not in response.content:
        print("✅ Réponse AJAX ne contient pas base.html")
    else:
        print("❌ Réponse AJAX contient encore base.html")
    
    # Vérifier que la réponse AJAX contient le file_list
    if b'fm-tbody' in response.content:
        print("✅ Réponse AJAX contient le file_list")
    else:
        print("❌ Réponse AJAX ne contient pas le file_list")


def test_folder_navigation():
    """Tester la navigation entre dossiers"""
    print("\n\n📁 TEST NAVIGATION DOSSIERS")
    print("=" * 50)
    
    # Obtenir le service pour l'utilisateur système
    import getpass
    system_user = getpass.getuser()
    service = get_system_user_service(system_user)
    
    print(f"Utilisateur: {system_user}")
    print(f"Racine: {service.base_path}")
    
    # Lister le contenu du home
    print("\n1️⃣ Test listing home directory:")
    result = service.list_directory(service.base_path)
    
    if result.get('success'):
        print(f"✅ Home directory listé: {result['path']}")
        print(f"   Nombre d'éléments: {len(result['items'])}")
        
        # Chercher des dossiers à tester
        folders = [item for item in result['items'] if item['is_dir']]
        
        if folders:
            print(f"   Dossiers trouvés: {[f['name'] for f in folders[:3]]}")
            
            # Tester la navigation vers le premier dossier
            test_folder = folders[0]
            print(f"\n2️⃣ Test navigation vers: {test_folder['name']}")
            
            folder_result = service.list_directory(test_folder['path'])
            if folder_result.get('success'):
                print(f"✅ Navigation réussie vers: {folder_result['path']}")
                print(f"   Éléments dans le dossier: {len(folder_result['items'])}")
            else:
                print(f"❌ Échec navigation: {folder_result.get('error')}")
        else:
            print("   Aucun dossier trouvé pour tester la navigation")
    else:
        print(f"❌ Erreur listing home: {result.get('error')}")


def test_security_paths():
    """Tester les chemins de sécurité"""
    print("\n\n🔐 TEST SÉCURITÉ CHEMINS")
    print("=" * 50)
    
    system_user = getpass.getuser()
    service = get_system_user_service(system_user)
    
    # Chemins qui devraient être interdits
    forbidden_paths = [
        '/',
        '/etc',
        '/usr/bin',
        '/var/log',
        '/boot',
        '/sys',
        '/proc'
    ]
    
    print("Test des chemins interdits:")
    for path in forbidden_paths:
        result = service.list_directory(path)
        if 'error' in result:
            print(f"✅ {path:15} -> INTERDIT")
        else:
            print(f"❌ {path:15} -> AUTORISÉ (PROBLÈME!)")
    
    # Chemins qui devraient être autorisés
    allowed_paths = [
        service.base_path,
        os.path.join(service.base_path, 'Documents'),
        os.path.join(service.base_path, 'Downloads')
    ]
    
    print("\nTest des chemins autorisés:")
    for path in allowed_paths:
        if os.path.exists(path):
            result = service.list_directory(path)
            if result.get('success'):
                print(f"✅ {path:30} -> AUTORISÉ")
            else:
                print(f"❌ {path:30} -> ERREUR: {result.get('error')}")
        else:
            print(f"⚠️  {path:30} -> INEXISTANT")


def test_path_operations():
    """Tester les opérations sur les chemins"""
    print("\n\n⚙️ TEST OPÉRATIONS CHEMINS")
    print("=" * 50)
    
    system_user = getpass.getuser()
    service = get_system_user_service(system_user)
    
    # Test création de dossier
    print("\n1️⃣ Test création dossier:")
    test_dir = os.path.join(service.base_path, 'test_navigation_folder')
    result = service.create_directory('test_navigation_folder', service.base_path)
    
    if result.get('success'):
        print(f"✅ Dossier créé: {result['path']}")
        
        # Vérifier qu'il existe
        if os.path.exists(test_dir):
            print("✅ Dossier vérifié sur le système")
            
            # Test suppression
            print("\n2️⃣ Test suppression dossier:")
            delete_result = service.delete_item(test_dir)
            if delete_result.get('success'):
                print("✅ Dossier supprimé avec succès")
                
                # Vérifier qu'il n'existe plus
                if not os.path.exists(test_dir):
                    print("✅ Dossier bien supprimé du système")
                else:
                    print("❌ Dossier existe encore sur le système")
            else:
                print(f"❌ Erreur suppression: {delete_result.get('error')}")
        else:
            print("❌ Dossier non trouvé sur le système")
    else:
        print(f"❌ Erreur création: {result.get('error')}")


def main():
    """Fonction principale de test"""
    print("🚀 TESTS NAVIGATION DYNAMIQUE")
    print(f"Utilisateur système: {getpass.getuser()}")
    print(f"FILE_MANAGER_ROOT: {settings.FILE_MANAGER_ROOT}")
    
    try:
        test_ajax_navigation()
        test_folder_navigation()
        test_security_paths()
        test_path_operations()
        
        print("\n\n🎉 TESTS TERMINÉS")
        print("La navigation dynamique est prête !")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
