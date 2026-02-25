// ==========================================
// navigation.js  —  FICHIER JS STATIQUE
// NE PAS utiliser {{ }} Django ici !
// Les données sont lues depuis le DOM (data-* du body).
// ==========================================

// Lire depuis data-current-path="..." sur le <body> (injecté par Django dans base.html)
let currentPath = document.body.dataset.currentPath
    || new URLSearchParams(window.location.search).get('path')
    || '/';

const rootPath = document.body.dataset.rootPath || currentPath;

const folderCache = new Map();
let loadingController = null;

// ── Naviguer vers un dossier ──────────────────────────────────
window.navigateToFolder = function(folderPath) {
    if (event) event.preventDefault();
    if (!folderPath || folderPath === '#') return;
    currentPath = folderPath;
    const newUrl = window.location.pathname + '?path=' + encodeURIComponent(folderPath);
    window.history.pushState({ path: folderPath }, '', newUrl);
    loadFolderContent(folderPath);
};

// ── Naviguer vers le dossier parent ──────────────────────────
window.navigateToParent = function() {
    if (event) event.preventDefault();
    const lastSlash = currentPath.lastIndexOf('/');
    const parentPath = lastSlash > 0 ? currentPath.substring(0, lastSlash) : rootPath;
    window.navigateToFolder(parentPath || rootPath);
};

// ── Naviguer en arrière/avant ─────────────────────────────────
window.navigateBack    = function() { if (event) event.preventDefault(); window.history.back(); };
window.navigateForward = function() { if (event) event.preventDefault(); window.history.forward(); };

// ── Recharger le dossier courant ──────────────────────────────
window.reloadCurrentFolder = function() {
    if (event) event.preventDefault();
    folderCache.delete(currentPath);
    const tb = document.getElementById('fm-tbody');
    if (!tb) { location.reload(); return; }
    tb.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:12px"><small style="opacity:.6">Actualisation…</small></td></tr>';
    fetch(window.location.pathname + '?path=' + encodeURIComponent(currentPath) + '&ajax=1&t=' + Date.now())
        .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); })
        .then(html => {
            const doc = new DOMParser().parseFromString(html, 'text/html');
            const nb  = doc.getElementById('fm-tbody');
            if (nb) { tb.innerHTML = nb.innerHTML; folderCache.set(currentPath, nb.innerHTML); attachFolderEvents(); }
            updateCurrentPathDisplay(currentPath);
        })
        .catch(err => { tb.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:12px;color:#ef4444"><small>Erreur : ' + err.message + '</small></td></tr>'; });
};

// ── Input de chemin ───────────────────────────────────────────
window.handlePathKeypress = function(e) { if (e.key === 'Enter') { e.preventDefault(); navigateFromPathInput(); } };
window.navigateFromPathInput = function() {
    const inp = document.getElementById('fm-path-input');
    if (!inp) return;
    const p = inp.value.trim();
    if (!p || !p.startsWith('/')) { inp.style.borderColor = '#ef4444'; setTimeout(() => { inp.style.borderColor = ''; }, 2000); return; }
    window.navigateToFolder(p);
};

// ── Charger le contenu d'un dossier ──────────────────────────
function loadFolderContent(path) {
    const tb = document.getElementById('fm-tbody');
    if (!tb) return;
    if (folderCache.has(path)) {
        tb.innerHTML = folderCache.get(path);
        updateCurrentPathDisplay(path);
        attachFolderEvents();
        return;
    }
    if (loadingController) loadingController.abort();
    loadingController = new AbortController();
    tb.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:12px"><small style="opacity:.6">Chargement…</small></td></tr>';
    fetch(window.location.pathname + '?path=' + encodeURIComponent(path) + '&ajax=1', { signal: loadingController.signal })
        .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); })
        .then(html => {
            const doc = new DOMParser().parseFromString(html, 'text/html');
            const nb  = doc.getElementById('fm-tbody');
            if (nb) {
                const content = nb.innerHTML;
                folderCache.set(path, content);
                if (folderCache.size > 20) folderCache.delete(folderCache.keys().next().value);
                tb.innerHTML = content;
                updateCurrentPathDisplay(path);
                attachFolderEvents();
            }
        })
        .catch(err => { if (err.name === 'AbortError') return; tb.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:12px;color:#ef4444"><small>Erreur : ' + err.message + '</small></td></tr>'; })
        .finally(() => { loadingController = null; });
}

// ── Mettre à jour l'affichage du chemin ───────────────────────
function updateCurrentPathDisplay(path) {
    currentPath = path;
    document.body.dataset.currentPath = path;
    const inp = document.getElementById('fm-path-input');
    if (inp) inp.value = path;
}

// ── Attacher les événements aux liens dossiers ────────────────
function attachFolderEvents() {
    document.querySelectorAll('#fm-tbody .fm-folder-link[data-path]').forEach(link => {
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);
        newLink.addEventListener('click', function(e) { e.preventDefault(); window.navigateToFolder(this.dataset.path); });
    });
    attachCheckboxEvents();
    updateToolbarState();
}

// ── Checkboxes + état toolbar ──────────────────────────────────
function attachCheckboxEvents() {
    const allCb  = document.getElementById('fm-check-all');
    const rowCbs = document.querySelectorAll('#fm-tbody .fm-checkbox');
    rowCbs.forEach(cb => {
        cb.addEventListener('change', function() {
            const row = this.closest('.fm-row');
            if (row) row.classList.toggle('fm-row--checked', this.checked);
            updateToolbarState();
        });
    });
    if (allCb) {
        allCb.addEventListener('change', function() {
            rowCbs.forEach(cb => { cb.checked = this.checked; const row = cb.closest('.fm-row'); if (row) row.classList.toggle('fm-row--checked', this.checked); });
            updateToolbarState();
        });
    }
}

function updateToolbarState() {
    const count = document.querySelectorAll('#fm-tbody .fm-checkbox:checked').length;
    document.querySelectorAll('.fm-action--sel').forEach(btn => btn.classList.toggle('fm-action--active', count > 0));
}

// ── Select All / Unselect All ─────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('btn-select-all')?.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('#fm-tbody .fm-checkbox').forEach(cb => { cb.checked = true; cb.closest('.fm-row')?.classList.add('fm-row--checked'); });
        const a = document.getElementById('fm-check-all'); if (a) a.checked = true;
        updateToolbarState();
    });
    document.getElementById('btn-unselect-all')?.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('#fm-tbody .fm-checkbox').forEach(cb => { cb.checked = false; cb.closest('.fm-row')?.classList.remove('fm-row--checked'); });
        const a = document.getElementById('fm-check-all'); if (a) a.checked = false;
        updateToolbarState();
    });
    attachFolderEvents();
});

// ── Boutons Précédent/Suivant du navigateur ────────────────────
window.addEventListener('popstate', function(e) {
    if (e.state && e.state.path) { currentPath = e.state.path; loadFolderContent(currentPath); }
});