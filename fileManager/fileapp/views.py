from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os
from datetime import datetime
from .services import get_system_user_service

_directory_cache = {}
_cache_timeout = 5


def home_view(request):
    user_context = getattr(request, 'user_context', {})
    if not user_context.get('is_authenticated'):
        return render(request, 'error.html', {'error': "Impossible de déterminer l'utilisateur système", 'user_context': user_context})
    file_service   = get_system_user_service(user_context['username'])
    requested_path = request.GET.get('path', user_context.get('current_path'))
    result         = file_service.list_directory(requested_path)
    if 'error' in result:
        return render(request, 'error.html', {'error': result['error'], 'user_context': user_context})
    folders, files = [], []
    for item in result['items']:
        item_data = {'name': item['name'], 'path': item['path'], 'size': format_size(item['size']),
                     'modified': format_datetime(item['modified']), 'permissions': item['permissions']}
        if item['is_dir']:
            folders.append(item_data)
        else:
            ext = os.path.splitext(item['name'])[1].lower().lstrip('.')
            item_data.update({'type': get_mime_type(item['name']), 'ext': ext or 'unknown'})
            files.append(item_data)
    folders.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())
    sidebar_tree = build_sidebar_tree(user_context['root_path'], result['path'])
    context = {'user_context': user_context, 'current_path': result['path'],
               'folders': folders, 'files': files, 'sidebar_tree': sidebar_tree,
               'system_info': user_context.get('system_info', {})}
    if request.GET.get('ajax') == '1':
        return render(request, 'components/file_list.html', context)
    return render(request, 'base.html', context)


def editor_view(request):
    user_context = getattr(request, 'user_context', {})
    if not user_context.get('is_authenticated'):
        return render(request, 'error.html', {'error': 'Non authentifié', 'user_context': user_context})
    file_path = request.GET.get('path', '').strip()
    if not file_path:
        return render(request, 'error.html', {'error': 'Chemin manquant', 'user_context': user_context})
    svc  = get_system_user_service(user_context['username'])
    real = svc._safe(file_path)
    if not real or not os.path.isfile(real):
        return render(request, 'error.html', {'error': 'Fichier introuvable ou accès refusé', 'user_context': user_context})
    encoding = request.GET.get('encoding', 'utf-8')
    try:
        with open(real, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
    except Exception as e:
        return render(request, 'error.html', {'error': str(e), 'user_context': user_context})
    file_name = os.path.basename(real)
    file_ext  = os.path.splitext(file_name)[1].lstrip('.') or 'txt'
    return render(request, 'editor.html', {
        'file_path': real, 'file_name': file_name,
        'file_dir': os.path.dirname(real), 'file_ext': file_ext,
        'file_content': content, 'user_context': user_context,
    })


@require_POST
def file_operations(request):
    user_context = getattr(request, 'user_context', {})
    if not user_context.get('is_authenticated'):
        return JsonResponse({'error': 'Non authentifié'}, status=403)
    svc = get_system_user_service(user_context['username'])
    op  = request.POST.get('operation', '').strip()

    if op == 'create_folder':
        result = svc.create_directory(
            request.POST.get('name', '').strip(),
            request.POST.get('parent_path', '').strip() or None)

    elif op == 'create_file':
        result = svc.create_file(
            request.POST.get('name', '').strip(),
            request.POST.get('parent_path', '').strip() or None)

    elif op == 'save_file':
        path     = request.POST.get('path', '').strip()
        content  = request.POST.get('content', '')
        encoding = request.POST.get('encoding', 'utf-8').strip()
        if not path:
            return JsonResponse({'error': 'Chemin requis'})
        real = svc._safe(path)
        if not real:
            return JsonResponse({'error': 'Accès non autorisé'})
        try:
            with open(real, 'w', encoding=encoding, errors='replace') as f:
                f.write(content)
            result = {'success': True}
        except PermissionError:
            result = {'error': 'Permission refusée'}
        except Exception as e:
            result = {'error': str(e)}

    elif op == 'delete':
        raw   = request.POST.get('paths', '') or request.POST.get('path', '')
        paths = [p.strip() for p in raw.split('|') if p.strip()]
        if not paths:
            return JsonResponse({'error': 'Aucun élément spécifié'})
        errors = []
        for p in paths:
            r = svc.delete_item(p)
            if 'error' in r:
                errors.append(r['error'])
        # Succès si AU MOINS UN élément supprimé
        if errors and len(errors) == len(paths):
            result = {'error': ' | '.join(errors)}
        else:
            result = {'success': True}
            if errors:
                result['warnings'] = ' | '.join(errors)

    elif op == 'move':
        raw_src  = request.POST.get('sources', '') or request.POST.get('source', '')
        dest_dir = request.POST.get('destination', '').strip()
        sources  = [s.strip() for s in raw_src.split('|') if s.strip()]
        if not sources or not dest_dir:
            return JsonResponse({'error': 'Source(s) et destination requises'})
        errors = []
        for src in sources:
            dest = os.path.join(dest_dir, os.path.basename(src))
            r = svc.move_item(src, dest)
            if 'error' in r:
                errors.append(r['error'])
        result = {'error': ' | '.join(errors)} if errors else {'success': True}

    elif op == 'copy':
        raw_src  = request.POST.get('sources', '') or request.POST.get('source', '')
        dest_dir = request.POST.get('destination', '').strip()
        sources  = [s.strip() for s in raw_src.split('|') if s.strip()]
        if not sources or not dest_dir:
            return JsonResponse({'error': 'Source(s) et destination requises'})
        errors = []
        for src in sources:
            dest = os.path.join(dest_dir, os.path.basename(src))
            r = svc.copy_item(src, dest)
            if 'error' in r:
                errors.append(r['error'])
        result = {'error': ' | '.join(errors)} if errors else {'success': True}

    elif op == 'rename':
        result = svc.rename_item(
            request.POST.get('path', '').strip(),
            request.POST.get('new_name', '').strip())

    elif op == 'chmod':
        result = svc.chmod_item(
            request.POST.get('path', '').strip(),
            request.POST.get('mode', '').strip())

    elif op == 'compress':
        raw_src = request.POST.get('sources', '').strip()
        sources = [s.strip() for s in raw_src.split('|') if s.strip()]
        result = svc.compress_items(
            sources,
            request.POST.get('destination', '').strip(),
            request.POST.get('format', 'zip').strip(),
            request.POST.get('include_hidden', '1') == '1',
            request.POST.get('follow_symlinks', '0') == '1')

    else:
        result = {'error': f'Opération inconnue : "{op}"'}

    return JsonResponse(result)


def format_size(size_bytes):
    if size_bytes == 0: return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024: return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_datetime(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%b %d, %Y, %I:%M %p")


def get_mime_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    return {
        '.txt':'text/plain','.json':'application/json','.php':'text/x-php',
        '.md':'text/markdown','.xml':'text/xml','.css':'text/css',
        '.js':'application/javascript','.html':'text/html','.png':'image/png',
        '.jpg':'image/jpeg','.jpeg':'image/jpeg','.gif':'image/gif',
        '.ico':'image/x-icon','.log':'text/plain','.py':'text/x-python',
        '.sh':'text/x-sh','.pdf':'application/pdf','.zip':'application/zip',
        '.tar':'application/x-tar',
    }.get(ext, 'application/octet-stream')


def build_sidebar_tree(root_path, current_path):
    import time
    key = f"tree_{root_path}_{current_path}"
    now = time.time()
    if key in _directory_cache:
        data, ts = _directory_cache[key]
        if now - ts < _cache_timeout: return data
    def _recurse(path, depth=0, max_depth=2):
        if depth >= max_depth: return []
        tree = []
        try:
            for name in sorted(os.listdir(path))[:50]:
                ip = os.path.join(path, name)
                if os.path.isdir(ip):
                    try: tree.append({'name': name, 'path': ip, 'is_current': ip == current_path, 'children': _recurse(ip, depth+1, max_depth)})
                    except (PermissionError, OSError): pass
        except (PermissionError, OSError): pass
        return tree
    result = [{'name': f'({os.path.basename(root_path)})', 'path': root_path, 'is_root': True, 'children': _recurse(root_path)}]
    _directory_cache[key] = (result, now)
    for k in [k for k, (_, ts) in list(_directory_cache.items()) if now - ts > _cache_timeout*2]: del _directory_cache[k]
    return result