import os
import shutil
import zipfile
import tarfile
import subprocess
from django.conf import settings
from django.contrib.auth.models import AnonymousUser


class FileOperationService:
    """
    Service pour les opérations sur les fichiers.
    L'espace de travail est strictement limité au home de l'utilisateur système.
    """

    def __init__(self, user_context):
        self.user_context = user_context
        self.base_path = os.path.realpath(user_context.get('root_path', ''))

    # ──────────────────────────────────────────────────────────────
    # HELPERS INTERNES
    # ──────────────────────────────────────────────────────────────

    def _safe(self, path):
        """
        Résout le chemin réel et vérifie qu'il reste dans base_path.
        Retourne le chemin résolu, ou None si hors zone.
        """
        if not path:
            return None
        real = os.path.realpath(str(path))
        # Le chemin doit commencer par base_path + '/' OU être exactement base_path
        if real == self.base_path or real.startswith(self.base_path + os.sep):
            return real
        return None

    def _auth_check(self):
        if not self.base_path:
            return {'error': 'Utilisateur non authentifié'}
        return None

    # ──────────────────────────────────────────────────────────────
    # LISTER UN RÉPERTOIRE
    # ──────────────────────────────────────────────────────────────

    def list_directory(self, path=None):
        if err := self._auth_check(): return err
        target = path or self.base_path
        real = self._safe(target)
        if not real:
            return {'error': 'Accès non autorisé'}
        try:
            items = []
            for name in os.listdir(real):
                item_path = os.path.join(real, name)
                try:
                    st = os.stat(item_path)
                    items.append({
                        'name': name,
                        'path': item_path,
                        'is_dir': os.path.isdir(item_path),
                        'size': st.st_size,
                        'modified': st.st_mtime,
                        'permissions': oct(st.st_mode)[-3:],
                    })
                except (PermissionError, OSError):
                    pass
            return {'success': True, 'path': real, 'items': items}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # CRÉER UN RÉPERTOIRE
    # ──────────────────────────────────────────────────────────────

    def create_directory(self, dir_name, parent_path=None):
        if err := self._auth_check(): return err
        parent = self._safe(parent_path or self.base_path)
        if not parent:
            return {'error': 'Accès non autorisé'}
        if not dir_name or '/' in dir_name or dir_name in ('.', '..'):
            return {'error': 'Nom de dossier invalide'}
        try:
            new_path = os.path.join(parent, dir_name)
            if os.path.exists(new_path):
                return {'error': f'"{dir_name}" existe déjà'}
            os.makedirs(new_path, exist_ok=False)
            return {'success': True, 'path': new_path}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # CRÉER UN FICHIER VIDE
    # ──────────────────────────────────────────────────────────────

    def create_file(self, file_name, parent_path=None):
        if err := self._auth_check(): return err
        parent = self._safe(parent_path or self.base_path)
        if not parent:
            return {'error': 'Accès non autorisé'}
        if not file_name or '/' in file_name or file_name in ('.', '..'):
            return {'error': 'Nom de fichier invalide'}
        try:
            new_path = os.path.join(parent, file_name)
            if os.path.exists(new_path):
                return {'error': f'"{file_name}" existe déjà'}
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write('')
            return {'success': True, 'path': new_path}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # SUPPRIMER UN FICHIER OU DOSSIER
    # ──────────────────────────────────────────────────────────────

    def delete_item(self, item_path):
        if err := self._auth_check(): return err
        real = self._safe(item_path)
        if not real:
            return {'error': 'Accès non autorisé'}
        # Interdire la suppression du répertoire racine lui-même
        if real == self.base_path:
            return {'error': 'Suppression du répertoire racine interdite'}
        try:
            if os.path.isdir(real):
                shutil.rmtree(real)
            else:
                os.remove(real)
            return {'success': True}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # DÉPLACER / RENOMMER
    # ──────────────────────────────────────────────────────────────

    def move_item(self, source_path, destination_path):
        if err := self._auth_check(): return err
        real_src = self._safe(source_path)
        if not real_src:
            return {'error': 'Source invalide ou accès non autorisé'}
        if not os.path.exists(real_src):
            return {'error': f'Source introuvable : {real_src}'}

        # La destination peut ne pas encore exister, on vérifie son parent
        real_dest = os.path.realpath(str(destination_path))
        dest_parent = os.path.dirname(real_dest)
        if not (real_dest == self.base_path or real_dest.startswith(self.base_path + os.sep)):
            return {'error': 'Destination hors de votre espace personnel'}
        if not os.path.exists(dest_parent):
            return {'error': f'Dossier destination introuvable : {dest_parent}'}

        try:
            shutil.move(real_src, real_dest)
            return {'success': True}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # COPIER
    # ──────────────────────────────────────────────────────────────

    def copy_item(self, source_path, destination_path):
        if err := self._auth_check(): return err
        real_src = self._safe(source_path)
        if not real_src:
            return {'error': 'Source invalide ou accès non autorisé'}
        if not os.path.exists(real_src):
            return {'error': f'Source introuvable : {real_src}'}

        real_dest = os.path.realpath(str(destination_path))
        dest_parent = os.path.dirname(real_dest)
        if not (real_dest == self.base_path or real_dest.startswith(self.base_path + os.sep)):
            return {'error': 'Destination hors de votre espace personnel'}
        if not os.path.exists(dest_parent):
            return {'error': f'Dossier destination introuvable : {dest_parent}'}
        if os.path.exists(real_dest):
            return {'error': f'Un élément portant ce nom existe déjà à la destination'}

        try:
            if os.path.isdir(real_src):
                shutil.copytree(real_src, real_dest)
            else:
                shutil.copy2(real_src, real_dest)
            return {'success': True}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # RENOMMER (alias move dans le même répertoire)
    # ──────────────────────────────────────────────────────────────

    def rename_item(self, item_path, new_name):
        if err := self._auth_check(): return err
        real_src = self._safe(item_path)
        if not real_src:
            return {'error': 'Élément invalide ou accès non autorisé'}
        if not os.path.exists(real_src):
            return {'error': f'Élément introuvable : {real_src}'}
        if not new_name or '/' in new_name or new_name in ('.', '..'):
            return {'error': 'Nouveau nom invalide'}

        parent_dir = os.path.dirname(real_src)
        real_dest = os.path.join(parent_dir, new_name)

        # Vérifie que la dest reste dans base_path
        if not (real_dest == self.base_path or real_dest.startswith(self.base_path + os.sep)):
            return {'error': 'Destination hors de votre espace personnel'}
        if os.path.exists(real_dest):
            return {'error': f'"{new_name}" existe déjà dans ce répertoire'}

        try:
            os.rename(real_src, real_dest)
            return {'success': True, 'new_path': real_dest}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # CHANGER LES PERMISSIONS (un seul élément)
    # ──────────────────────────────────────────────────────────────

    def chmod_item(self, item_path, mode_str):
        if err := self._auth_check(): return err
        real = self._safe(item_path)
        if not real:
            return {'error': 'Accès non autorisé'}
        if not os.path.exists(real):
            return {'error': f'Élément introuvable : {real}'}
        if not mode_str or not all(c in '01234567' for c in str(mode_str)) or len(str(mode_str)) != 3:
            return {'error': 'Mode invalide (ex: 644, 755, 777)'}
        try:
            os.chmod(real, int(str(mode_str), 8))
            return {'success': True}
        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}

    # ──────────────────────────────────────────────────────────────
    # COMPRESSER
    # ──────────────────────────────────────────────────────────────

    def compress_items(self, source_paths, destination_path, fmt='zip',
                       include_hidden=True, follow_symlinks=False):
        if err := self._auth_check(): return err

        # Valider toutes les sources
        real_sources = []
        for sp in source_paths:
            r = self._safe(sp)
            if not r:
                return {'error': f'Source non autorisée : {sp}'}
            if not os.path.exists(r):
                return {'error': f'Source introuvable : {r}'}
            real_sources.append(r)

        if not real_sources:
            return {'error': 'Aucune source valide'}

        # Valider la destination
        real_dest = os.path.realpath(str(destination_path))
        dest_parent = os.path.dirname(real_dest)
        if not (real_dest == self.base_path or real_dest.startswith(self.base_path + os.sep)):
            return {'error': 'Destination hors de votre espace personnel'}
        if not os.path.exists(dest_parent):
            return {'error': f'Dossier destination introuvable : {dest_parent}'}

        try:
            if fmt == 'zip':
                with zipfile.ZipFile(real_dest, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for src in real_sources:
                        if os.path.isdir(src):
                            for root, dirs, files in os.walk(src,
                                    followlinks=follow_symlinks):
                                if not include_hidden:
                                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                                    files = [f for f in files if not f.startswith('.')]
                                for fname in files:
                                    fp = os.path.join(root, fname)
                                    arcname = os.path.relpath(fp, os.path.dirname(src))
                                    zf.write(fp, arcname)
                        else:
                            if include_hidden or not os.path.basename(src).startswith('.'):
                                zf.write(src, os.path.basename(src))

            elif fmt in ('tar', 'tar.gz'):
                mode = 'w:gz' if fmt == 'tar.gz' else 'w'
                with tarfile.open(real_dest, mode) as tf:
                    for src in real_sources:
                        def _filter(tarinfo):
                            name = os.path.basename(tarinfo.name)
                            if not include_hidden and name.startswith('.'):
                                return None
                            return tarinfo
                        tf.add(src, arcname=os.path.basename(src), filter=_filter)

            elif fmt == '7z':
                if not shutil.which('7z'):
                    return {'error': '7z n\'est pas installé (sudo apt install p7zip-full)'}
                cmd = ['7z', 'a', real_dest] + real_sources
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode != 0:
                    return {'error': proc.stderr.strip() or 'Erreur 7z'}
            else:
                return {'error': f'Format non supporté : {fmt}'}

            return {'success': True, 'path': real_dest}

        except PermissionError:
            return {'error': 'Permission refusée'}
        except Exception as e:
            return {'error': str(e)}


# ══════════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def get_system_user_service(username):
    """Service pour un utilisateur système (application locale)."""
    base_dir = os.path.realpath(settings.FILE_MANAGER_ROOT)
    user_home = os.path.expanduser(f"~{username}")
    if not os.path.exists(user_home):
        user_home = os.path.join(base_dir, username)
        os.makedirs(user_home, exist_ok=True)

    try:
        import grp
        sudo_groups = ['sudo', 'wheel', 'admin']
        user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        is_admin = any(group in sudo_groups for group in user_groups)
    except Exception:
        is_admin = False

    user_context = {
        'is_authenticated': True,
        'username': username,
        'is_system_user': True,
        'is_admin': is_admin,
        'root_path': user_home,
        'current_path': user_home,
        'can_access_system': is_admin,
    }
    return FileOperationService(user_context)


def get_user_service(user):
    """Service pour un utilisateur Django (legacy)."""
    from fileManager.middleware import FileSecurityMiddleware
    if isinstance(user, AnonymousUser):
        user_context = {
            'is_authenticated': False,
            'root_path': None,
            'current_path': None,
            'can_access_system': False,
        }
    else:
        base_dir = os.path.realpath(settings.FILE_MANAGER_ROOT)
        user_root = base_dir if user.is_superuser else os.path.join(base_dir, user.username)
        os.makedirs(user_root, exist_ok=True)
        user_context = {
            'is_authenticated': True,
            'username': user.username,
            'is_superuser': user.is_superuser,
            'root_path': user_root,
            'current_path': user_root,
            'can_access_system': user.is_superuser,
        }
    return FileOperationService(user_context)