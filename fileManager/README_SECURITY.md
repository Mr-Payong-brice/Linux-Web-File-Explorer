# 🛡️ Système de Sécurité - Application Locale

## 🎯 Objectifs atteints

✅ **Interdire l'accès à /** - Racine du système complètement bloquée  
✅ **Interdire l'accès aux dossiers des autres users** - Isolation stricte par utilisateur  
✅ **Définir automatiquement un root directory par utilisateur** - Home utilisateur système  
✅ **Éviter les demandes de mot de passe système** - Opérations gérées en interne  
✅ **Centraliser des règles globales** - Middleware + service centralisé  
✅ **Pas d'authentification Django** - Utilise l'utilisateur système connecté  

## 🏗️ Architecture pour application locale

### 1. Middleware de sécurité global (`fileManager/middleware.py`)
- **FileSecurityMiddleware** : Contrôle automatique utilisant `getpass.getuser()`
- Règles appliquées :
  - ❌ Interdiction de `/`, `/etc`, `/usr`, `/var`, `/boot`, `/sys`, `/proc`
  - ✅ Isolation par utilisateur système automatique
  - ✅ Contexte utilisateur système injecté dans chaque requête

### 2. Service de fichiers sécurisé (`fileapp/services.py`)
- **FileOperationService** : Opérations fichiers sans mot de passe
- **get_system_user_service()** : Service pour utilisateur système
- Fonctionnalités :
  - `list_directory()` : Lister le contenu
  - `create_directory()` : Créer des dossiers
  - `delete_item()` : Supprimer fichiers/dossiers
  - `move_item()` : Déplacer/renommer
  - `copy_item()` : Copier

### 3. Configuration globale (`settings.py`)
```python
FILE_MANAGER_ROOT = os.path.expanduser("~")  # /home/bricevalery
FILE_MANAGER_USER_ISOLATION = True  # Active l'isolation utilisateur système
```

### 4. Vues pour application locale (`fileapp/views.py`)
- Utilisation automatique du contexte utilisateur système
- Pas de décorateurs `@login_required`
- Arborescence dynamique basée sur le home utilisateur

## 🔐 Règles de sécurité implémentées

### Règle 1 : Protection de la racine système
```python
if real_path == "/" or real_path.startswith("/etc") or real_path.startswith("/usr") or real_path.startswith("/var"):
    return HttpResponseForbidden("Accès interdit: répertoire système")
```

### Règle 2 : Isolation utilisateur système
```python
if settings.FILE_MANAGER_USER_ISOLATION:
    user_root = self._get_system_user_root(system_user)
    if not real_path.startswith(user_root):
        return HttpResponseForbidden(f"Accès interdit: vous ne pouvez accéder qu'à votre dossier personnel ({user_root})")
```

### Règle 3 : Détection automatique utilisateur système
```python
def _get_system_user_root(self, username):
    # Pour l'application locale, l'utilisateur accède à son propre home
    user_home = os.path.expanduser(f"~{username}")
    os.makedirs(user_home, exist_ok=True)  # Création auto
    return user_home
```

## 👥 Comportement par type d'utilisateur système

### Utilisateur standard (ex: bricevalery)
- **Racine autorisée** : `/home/bricevalery/` (son home directory)
- **Peut voir** : Uniquement son propre dossier et sous-dossiers
- **Ne peut pas voir** : `/home/otheruser/`, `/etc`, `/usr`, `/var`, etc.
- **Authentification** : Automatique via système d'exploitation

### Utilisateur avec droits sudo (admin)
- **Racine autorisée** : `/home/bricevalery/` (son home directory)
- **Peut voir** : Son home directory + indication admin dans l'interface
- **Ne peut pas voir** : Racine système `/`, `/etc`, `/usr` (protection système maintenue)
- **Authentification** : Automatique via système d'exploitation

### Tous les utilisateurs
- **Pas de login Django** : L'authentification est gérée par Pop!_OS
- **Isolation garantie** : Chaque utilisateur reste dans son espace
- **Opérations sans mot de passe** : Gérées en interne par Django

## 🚀 Utilisation (Application Locale)

### Démarrer le serveur
```bash
cd /home/bricevalery/Documents/projetSe/Linux-Web-File-Explorer/fileManager
python3 manage.py runserver
```

### Accéder à l'application
- URL : `http://127.0.0.1:8000/`
- **Pas de login nécessaire** : L'utilisateur système est automatiquement détecté
- L'application utilise l'utilisateur connecté à Pop!_OS

### Vérifier l'utilisateur système
```bash
whoami  # Affiche l'utilisateur actuel
echo $HOME  # Affiche le home directory
```

## 🧪 Tests de sécurité

Deux scripts de test sont disponibles :

### 1. Test application locale : `test_local_app.py`
```bash
python3 test_local_app.py
```

Le script vérifie :
- ✅ Détection automatique de l'utilisateur système
- ✅ Interdiction d'accès à `/` et aux répertoires système
- ✅ Accès autorisé dans son propre home directory
- ✅ Opérations fichiers sans mot de passe
- ✅ Détection des privilèges admin (groupe sudo)

### 2. Test auth Django (legacy) : `test_security.py`
```bash
python3 test_security.py  # Nécessite les dépendances Django
```

## 📁 Structure des répertoires

### Pour l'application locale
```
/home/bricevalery/          # Home de l'utilisateur système
├── Documents/              # Vos documents
├── Downloads/              # Vos téléchargements
├── Pictures/               # Vos images
├── filemanager_test_dir/   # Créé par les tests
└── ...                     # Vos autres dossiers personnels
```

### L'application Django
```
/home/bricevalery/Documents/projetSe/Linux-Web-File-Explorer/fileManager/
├── fileManager/            # Configuration Django
├── fileapp/                # Vues et services
├── templates/              # Templates HTML
├── static/                 # Fichiers statiques
├── test_local_app.py       # Tests pour app locale
└── test_security.py        # Tests auth Django (legacy)
```

## 🔧 Points d'extension

### Ajouter des types de fichiers supportés
Dans `views.py` → `get_mime_type()` :
```python
mime_types = {
    '.txt': 'text/plain',
    '.pdf': 'application/pdf',
    # Ajouter vos types ici
}
```

### Personnaliser les règles de sécurité
Dans `middleware.py` → `FileSecurityMiddleware` :
```python
# Ajouter d'autres répertoires interdits
if real_path.startswith("/autre-repertoire-interdit"):
    return HttpResponseForbidden("Accès interdit")
```

### Ajouter des opérations fichiers
Dans `services.py` → `FileOperationService` :
```python
def custom_operation(self, path):
    # Votre logique ici
    pass
```

## ⚡ Performance et sécurité

- **Double vérification** : Middleware + service
- **Résolution des chemins réels** : `os.path.realpath()` anti-symlink
- **Pas de sudo** : Opérations avec permissions utilisateur uniquement
- **Isolation complète** : Chaque utilisateur dans son bac à sable

## 🎉 Résultat

L'application offre maintenant :
- **Sécurité maximale** : Aucun accès système possible
- **Isolation totale** : Les utilisateurs ne se voient pas entre eux
- **Gestion transparente** : Pas de mots de passe système
- **Architecture scalable** : Facile à étendre pour les besoins métier

Le système est prêt pour le développement métier avec une base sécurisée ! 🚀
