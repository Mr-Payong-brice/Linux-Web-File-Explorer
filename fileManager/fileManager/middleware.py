import os
import getpass
from django.conf import settings
from django.http import HttpResponseForbidden

# Chemins système interdits
BLOCKED_PATHS = ('/etc', '/usr', '/var', '/boot', '/sys', '/proc', '/root', '/bin', '/sbin', '/lib', '/lib64')


class FileSecurityMiddleware:
    """
    Middleware de sécurité pour le file manager local.
    - Utilise l'utilisateur système connecté (pas d'auth Django)
    - Interdit l'accès aux dossiers système critiques
    - Isole chaque utilisateur dans son home
    - NE bloque PAS les requêtes POST internes (file-operations/)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.base_dir = os.path.realpath(settings.FILE_MANAGER_ROOT)

    def __call__(self, request):
        system_user = getpass.getuser()

        # ── Validation du chemin de NAVIGATION (GET uniquement) ──
        # On ne valide le chemin que pour les requêtes GET de navigation
        # Les requêtes POST vers /file-operations/ ont leur propre validation
        # dans le service (méthode _safe)
        if request.method == 'GET':
            requested_path = request.GET.get('path')
            if requested_path:
                real_path = os.path.realpath(requested_path)

                # Bloquer la racine et les chemins système
                if real_path == '/' or any(real_path.startswith(p) for p in BLOCKED_PATHS):
                    return HttpResponseForbidden("Accès interdit : répertoire système")

                # Isolation par utilisateur
                if getattr(settings, 'FILE_MANAGER_USER_ISOLATION', True):
                    user_root = self._get_system_user_root(system_user)
                    if not (real_path == user_root or real_path.startswith(user_root + os.sep)):
                        return HttpResponseForbidden(
                            f"Accès interdit : vous ne pouvez accéder qu'à votre dossier personnel ({user_root})"
                        )
                else:
                    if not real_path.startswith(self.base_dir):
                        return HttpResponseForbidden("Accès interdit : hors de la zone autorisée")

        # ── Ajouter le contexte utilisateur à la requête ─────────
        request.user_context = self._build_system_user_context(system_user)

        return self.get_response(request)

    def _get_system_user_root(self, username):
        user_home = os.path.expanduser(f"~{username}")
        if not os.path.exists(user_home):
            user_home = os.path.join(self.base_dir, username)
            os.makedirs(user_home, exist_ok=True)
        return os.path.realpath(user_home)

    def _build_system_user_context(self, username):
        user_root = self._get_system_user_root(username)

        try:
            import grp
            sudo_groups = ['sudo', 'wheel', 'admin']
            user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
            is_admin = any(group in sudo_groups for group in user_groups)
        except Exception:
            is_admin = False

        return {
            'is_authenticated':  True,
            'username':          username,
            'is_system_user':    True,
            'is_admin':          is_admin,
            'root_path':         user_root,
            'current_path':      user_root,
            'can_access_system': is_admin,
            'system_info': {
                'home_dir':          os.path.expanduser('~'),
                'current_dir':       os.getcwd(),
                'file_manager_root': self.base_dir,
            }
        }