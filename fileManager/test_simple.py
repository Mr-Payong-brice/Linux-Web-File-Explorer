#!/usr/bin/env python3
"""
Test simple sans Django pour vérifier la logique de base
"""

import os
import getpass

def test_system_detection():
    """Test basique de détection utilisateur"""
    print("👤 TEST DÉTECTION UTILISATEUR SYSTÈME")
    print("=" * 50)
    
    system_user = getpass.getuser()
    home_dir = os.path.expanduser('~')
    
    print(f"Utilisateur système: {system_user}")
    print(f"Home directory: {home_dir}")
    print(f"Home existe: {os.path.exists(home_dir)}")
    
    # Test de sécurité
    forbidden_paths = ['/', '/etc', '/usr', '/var', '/boot', '/sys', '/proc']
    print(f"\n🔐 TEST SÉCURITÉ DE BASE")
    print("=" * 30)
    
    for path in forbidden_paths:
        real_path = os.path.realpath(path)
        is_forbidden = (
            real_path == "/" or 
            real_path.startswith("/etc") or 
            real_path.startswith("/usr") or 
            real_path.startswith("/var") or
            real_path.startswith("/boot") or
            real_path.startswith("/sys") or
            real_path.startswith("/proc")
        )
        status = "✅ INTERDIT" if is_forbidden else "❌ AUTORISÉ"
        print(f"{path:12} -> {status}")
    
    # Test accès home
    print(f"\n📁 TEST ACCÈS HOME")
    print("=" * 25)
    home_real = os.path.realpath(home_dir)
    can_access_home = os.path.exists(home_real) and os.access(home_real, os.R_OK)
    print(f"Home accessible: {'✅ OUI' if can_access_home else '❌ NON'}")
    
    if can_access_home:
        try:
            items = os.listdir(home_real)
            print(f"Nombre d'éléments dans home: {len(items)}")
            
            # Afficher quelques éléments
            for i, item in enumerate(items[:5]):
                item_path = os.path.join(home_real, item)
                is_dir = os.path.isdir(item_path)
                icon = "📁" if is_dir else "📄"
                print(f"  {icon} {item}")
            
            if len(items) > 5:
                print(f"  ... et {len(items) - 5} autres éléments")
                
        except PermissionError:
            print("❌ Permission refusée pour lister le home")
    
    # Test création répertoire
    print(f"\n📂 TEST CRÉATION RÉPERTOIRE")
    print("=" * 30)
    test_dir = os.path.join(home_real, "filemanager_test_simple")
    
    try:
        os.makedirs(test_dir, exist_ok=True)
        if os.path.exists(test_dir):
            print(f"✅ Répertoire créé: {test_dir}")
            # Nettoyer
            os.rmdir(test_dir)
            print(f"✅ Répertoire nettoyé")
        else:
            print(f"❌ Échec création répertoire")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print(f"\n🎉 TEST TERMINÉ")
    print("L'environnement système est prêt pour l'application Django !")

if __name__ == '__main__':
    test_system_detection()
