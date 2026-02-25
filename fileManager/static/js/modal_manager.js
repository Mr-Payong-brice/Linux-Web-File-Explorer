/* ============================================================
   modal_manager.js  —  Gestionnaire des 5 modals
   ============================================================ */

(function () {
    'use strict';

    // ══════════════════════════════════════════════════════════
    // HELPERS GLOBAUX
    // ══════════════════════════════════════════════════════════

    const ICONS = {
        folder: `<path d="M1 3.5A1.5 1.5 0 0 1 2.5 2h2.764c.958 0 1.76.56 2.311 1.184C7.985 3.648 8.48 4 9 4h4.5A1.5 1.5 0 0 1 15 5.5v7a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5v-9z"/>`,
        file:   `<path d="M4 0h5.293A1 1 0 0 1 10 .293L13.707 4a1 1 0 0 1 .293.707V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm5.5 1.5v2a1 1 0 0 0 1 1h2l-3-3z"/>`,
    };

    function esc(str) {
        const d = document.createElement('div');
        d.textContent = String(str || '');
        return d.innerHTML;
    }

    function getCurrentPath() {
        if (typeof currentPath !== 'undefined' && currentPath) return currentPath;
        const inp = document.getElementById('fm-path-input');
        if (inp && inp.value) return inp.value;
        return document.body.dataset.currentPath || '/';
    }

    function getRootPath() {
        return document.body.dataset.rootPath || '/';
    }

    /**
     * Récupère les éléments sélectionnés dans le tbody.
     * Robuste : supporte data-path, onclick=navigateToFolder, fallback currentPath+nom
     */
    function getSelectedItems() {
        var items = [];
        // Cherche toutes les rows dont la checkbox est cochée
        // OU qui portent une classe de sélection
        document.querySelectorAll('#fm-tbody .fm-row').forEach(function(row) {
            var cb = row.querySelector('.fm-checkbox');
            var isSelected = (cb && cb.checked)
                || row.classList.contains('fm-row--selected')
                || row.classList.contains('selected')
                || row.classList.contains('active');
            if (!isSelected) return;

            // data-path d'abord sur le <tr>, sinon sur le lien
            var path = row.dataset.path || '';
            if (!path) {
                var link = row.querySelector('[data-path]');
                if (link) path = link.dataset.path || '';
            }
            // Fallback : construire depuis currentPath + data-name
            if (!path) {
                var name = row.dataset.name || '';
                if (name) path = getCurrentPath().replace(/\/+$/, '') + '/' + name;
            }
            if (!path || path === '#') return;

            var name = row.dataset.name
                || row.querySelector('.fm-file-link, .fm-folder-link')?.textContent?.trim()
                || '';
            var isFolder = row.classList.contains('fm-row--folder')
                || row.dataset.type === 'folder';

            path = path.replace(/\/\/+/g, '/');
            items.push({ name: name, path: path, type: isFolder ? 'folder' : 'file' });
        });
        console.debug('[FM] getSelectedItems =>', items);
        return items;
    }

    function getCsrf() {
        var el = document.querySelector('[name=csrfmiddlewaretoken]');
        if (el) return el.value;
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    async function apiCall(data) {
        var body = new FormData();
        Object.entries(data).forEach(function(kv) { body.append(kv[0], kv[1]); });
        body.append('csrfmiddlewaretoken', getCsrf());
        var res = await fetch('/file-operations/', {
            method: 'POST', body: body,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    }

    function itemHtml(item) {
        var isFolder = item.type === 'folder';
        return '<div class="fm-modal__selected-item">' +
            '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" class="' +
            (isFolder ? 'fm-modal__folder-icon' : 'fm-modal__file-icon') + '">' +
            (isFolder ? ICONS.folder : ICONS.file) + '</svg>' +
            '<span class="fm-modal__file-name">' + esc(item.name) + '</span>' +
            '<span style="margin-left:auto;font-size:10px;opacity:.4;font-family:monospace;' +
            'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px" title="' +
            esc(item.path) + '">' + esc(item.path) + '</span></div>';
    }

    // ══════════════════════════════════════════════════════════
    // TOAST
    // ══════════════════════════════════════════════════════════

    function toast(msg, type) {
        type = type || 'success';
        var box = document.getElementById('fm-toast-box');
        if (!box) {
            box = document.createElement('div');
            box.id = 'fm-toast-box';
            Object.assign(box.style, {
                position:'fixed', top:'18px', right:'18px', zIndex:'99999',
                display:'flex', flexDirection:'column', gap:'8px', pointerEvents:'none'
            });
            document.body.appendChild(box);
        }
        if (!document.getElementById('fm-toast-css')) {
            var s = document.createElement('style');
            s.id = 'fm-toast-css';
            s.textContent = '@keyframes _tin{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:none}}' +
                '@keyframes _tout{to{opacity:0;transform:translateX(24px)}}' +
                '@keyframes _spin{to{transform:rotate(360deg)}}';
            document.head.appendChild(s);
        }
        var colors = { success:'#22c55e', error:'#ef4444', warning:'#f59e0b', info:'#3b82f6' };
        var svgMap = {
            success:'<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>',
            error:  '<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293z"/>',
            warning:'<path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767zm-1.8 4.687.35 3.508a.552.552 0 0 0 1.1 0l.35-3.508A.905.905 0 0 0 8 5a.905.905 0 0 0-.818 1.253zM8 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>',
            info:   '<path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>'
        };
        var el = document.createElement('div');
        Object.assign(el.style, {
            display:'flex', alignItems:'center', gap:'10px', padding:'11px 16px',
            borderRadius:'8px', background: colors[type] || colors.info, color:'#fff',
            fontSize:'13px', fontWeight:'500', pointerEvents:'all',
            boxShadow:'0 4px 18px rgba(0,0,0,.28)', minWidth:'240px', maxWidth:'370px',
            animation:'_tin .22s ease forwards'
        });
        el.innerHTML = '<svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" style="flex-shrink:0">' +
            (svgMap[type] || svgMap.info) + '</svg><span>' + esc(msg) + '</span>';
        box.appendChild(el);
        setTimeout(function() {
            el.style.animation = '_tout .22s ease forwards';
            setTimeout(function() { el.remove(); }, 230);
        }, 3800);
    }

    // ══════════════════════════════════════════════════════════
    // LOADER BOUTON
    // ══════════════════════════════════════════════════════════

    function setLoading(btn, on) {
        if (!btn) return;
        if (on) {
            btn._orig = btn.innerHTML;
            btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" ' +
                'style="animation:_spin .6s linear infinite;display:inline-block">' +
                '<path d="M8 1a7 7 0 1 0 7 7h-1.5A5.5 5.5 0 1 1 8 2.5V1z"/></svg> …';
            btn.disabled = true;
        } else {
            if (btn._orig !== undefined) btn.innerHTML = btn._orig;
            btn.disabled = false;
        }
    }

    // ══════════════════════════════════════════════════════════
    // OVERLAY
    // ══════════════════════════════════════════════════════════

    function openOverlay(id) {
        var el = document.getElementById(id);
        if (el) { el.classList.add('active'); document.body.style.overflow = 'hidden'; }
    }
    function closeOverlay(id) {
        var el = document.getElementById(id);
        if (el) { el.classList.remove('active'); document.body.style.overflow = ''; }
    }
    function isOpen(id) {
        var el = document.getElementById(id);
        return el ? el.classList.contains('active') : false;
    }

    // ══════════════════════════════════════════════════════════
    // REFRESH
    // ══════════════════════════════════════════════════════════

    function refreshFolder() {
        if (typeof folderCache !== 'undefined') {
            try { folderCache.clear(); } catch(e) { folderCache.delete(getCurrentPath()); }
        }
        if (typeof reloadCurrentFolder === 'function') {
            reloadCurrentFolder();
        } else {
            var p  = getCurrentPath();
            var tb = document.getElementById('fm-tbody');
            if (!tb) { location.reload(); return; }
            tb.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:12px">' +
                '<small style="opacity:.6">Actualisation…</small></td></tr>';
            fetch(location.pathname + '?path=' + encodeURIComponent(p) + '&ajax=1&t=' + Date.now())
                .then(function(r) { return r.text(); })
                .then(function(html) {
                    var doc = new DOMParser().parseFromString(html, 'text/html');
                    var nb  = doc.getElementById('fm-tbody');
                    if (nb) tb.innerHTML = nb.innerHTML;
                    if (typeof attachFolderEvents === 'function') attachFolderEvents();
                })
                .catch(function() { toast('Erreur de rafraîchissement', 'error'); });
        }
    }

    // ══════════════════════════════════════════════════════════
    // PATH-PICKER
    // ══════════════════════════════════════════════════════════

    function attachPathPicker(input) {
        if (!input || input._pickerAttached) return;
        input._pickerAttached = true;
        input.setAttribute('autocomplete', 'off');
        var dd = null, timer = null;

        function removeDd() { if (dd) { dd.remove(); dd = null; } }

        function makeDd() {
            removeDd();
            dd = document.createElement('div');
            var rect = input.getBoundingClientRect();
            Object.assign(dd.style, {
                position:'fixed', zIndex:'99998',
                top: (rect.bottom + 2) + 'px', left: rect.left + 'px',
                width: rect.width + 'px', background:'#1e1e2e',
                border:'1px solid #45475a', borderRadius:'6px',
                boxShadow:'0 6px 20px rgba(0,0,0,.4)',
                maxHeight:'200px', overflowY:'auto', fontSize:'12px'
            });
            document.body.appendChild(dd);
        }

        async function suggest(val) {
            var root = getRootPath();
            var lastSlash = val.lastIndexOf('/');
            var parentDir = lastSlash > 0 ? val.slice(0, lastSlash) : root;
            var prefix    = val.slice(lastSlash + 1).toLowerCase();
            if (!parentDir.startsWith(root)) parentDir = root;
            try {
                var r = await fetch(
                    location.pathname + '?path=' + encodeURIComponent(parentDir) + '&ajax=1',
                    { headers: { 'X-Requested-With': 'XMLHttpRequest' } }
                );
                var html = await r.text();
                var doc  = new DOMParser().parseFromString(html, 'text/html');
                var links = doc.querySelectorAll('.fm-folder-link[data-path], .fm-folder-link[onclick]');
                var list = [];
                links.forEach(function(l) {
                    var p = l.dataset.path;
                    if (!p) {
                        var m = (l.getAttribute('onclick') || '').match(/navigateToFolder\s*\(\s*['"]([^'"]+)['"]\s*\)/);
                        if (m) p = m[1];
                    }
                    if (!p) return;
                    var n = (l.textContent.trim() || '').toLowerCase();
                    if (!prefix || n.startsWith(prefix)) list.push({ path: p, name: l.textContent.trim() });
                });
                return list;
            } catch(e) { return []; }
        }

        function renderSugg(items) {
            if (!items.length) { removeDd(); return; }
            makeDd();
            items.forEach(function(item) {
                var row = document.createElement('div');
                Object.assign(row.style, {
                    padding:'7px 12px', cursor:'pointer',
                    display:'flex', alignItems:'center', gap:'8px', color:'#cdd6f4'
                });
                row.innerHTML = '<svg width="11" height="11" viewBox="0 0 16 16" fill="#89b4fa">' +
                    ICONS.folder + '</svg><span>' + esc(item.path) + '</span>';
                row.addEventListener('mouseenter', function() { row.style.background='rgba(137,180,250,.15)'; });
                row.addEventListener('mouseleave', function() { row.style.background=''; });
                row.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    input.value = item.path;
                    removeDd();
                });
                dd.appendChild(row);
            });
        }

        input.addEventListener('input', function() {
            clearTimeout(timer);
            var v = input.value.trim();
            if (!v) { removeDd(); return; }
            timer = setTimeout(async function() { renderSugg(await suggest(v)); }, 220);
        });
        input.addEventListener('focus', function() {
            if (!input.value) input.value = getCurrentPath();
        });
        document.addEventListener('click', function(e) {
            if (dd && e.target !== input && !dd.contains(e.target)) removeDd();
        }, true);
    }

    // ══════════════════════════════════════════════════════════
    // MODAL 1 — NEW FILE / NEW FOLDER
    // ══════════════════════════════════════════════════════════

    (function() {
        var OVR      = 'fm-modal-overlay';
        var titleEl  = document.getElementById('fm-modal-title');
        var createBtn= document.getElementById('fm-modal-create');
        var cancelBtn= document.getElementById('fm-modal-cancel');
        var closeBtn = document.getElementById('fm-modal-close');
        var nameInp  = document.getElementById('fm-item-name');
        var pathInp  = document.getElementById('fm-item-path');
        var labelEl  = document.querySelector('label[for="fm-item-name"]');
        if (!titleEl) return;

        var type = 'file';

        function open(t) {
            type = t;
            var isFolder = t === 'folder';
            titleEl.textContent   = isFolder ? 'New Folder' : 'New File';
            createBtn.textContent = isFolder ? 'Create Folder' : 'Create File';
            if (labelEl) labelEl.textContent = isFolder ? 'Folder name:' : 'File name:';
            nameInp.placeholder = isFolder
                ? '(ex: my-folder, documents)'
                : '(ex: index.html, script.py, notes.txt)';
            nameInp.value = '';
            if (pathInp) pathInp.value = getCurrentPath();
            openOverlay(OVR);
            nameInp.focus();
        }

        async function doCreate() {
            var name = nameInp.value.trim();
            if (!name) { nameInp.focus(); toast('Entrez un nom.', 'warning'); return; }
            if (/[\/\\<>:"|?*\x00-\x1f]/.test(name)) { toast('Nom invalide.', 'error'); return; }
            var parent = pathInp ? pathInp.value.trim() : getCurrentPath();
            setLoading(createBtn, true);
            try {
                var r = await apiCall({
                    operation: type === 'folder' ? 'create_folder' : 'create_file',
                    name: name, parent_path: parent
                });
                if (r.error) { toast(r.error, 'error'); }
                else { toast('"' + name + '" créé avec succès.', 'success'); closeOverlay(OVR); refreshFolder(); }
            } catch(e) { toast('Erreur réseau : ' + e.message, 'error'); }
            finally    { setLoading(createBtn, false); }
        }

        var newFileBtn   = document.querySelector('[data-action="new-file"]');
        var newFolderBtn = document.querySelector('[data-action="new-folder"]');
        if (newFileBtn)   newFileBtn.addEventListener('click',   function(e) { e.preventDefault(); open('file'); });
        if (newFolderBtn) newFolderBtn.addEventListener('click', function(e) { e.preventDefault(); open('folder'); });
        if (createBtn) createBtn.addEventListener('click', doCreate);
        if (cancelBtn) cancelBtn.addEventListener('click', function() { closeOverlay(OVR); });
        if (closeBtn)  closeBtn.addEventListener('click',  function() { closeOverlay(OVR); });
        if (nameInp)   nameInp.addEventListener('keydown', function(e) { if (e.key === 'Enter') doCreate(); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && isOpen(OVR)) closeOverlay(OVR); });
    })();

    // ══════════════════════════════════════════════════════════
    // MODAL 2 — COPY / MOVE / RENAME
    // ══════════════════════════════════════════════════════════

    (function() {
        var OVR        = 'fm-action-modal-overlay';
        var titleEl    = document.getElementById('fm-action-modal-title');
        var confirmBtn = document.getElementById('fm-action-modal-confirm');
        var cancelBtn  = document.getElementById('fm-action-modal-cancel');
        var closeBtn   = document.getElementById('fm-action-modal-close');
        var actionInp  = document.getElementById('fm-action-input');
        var labelEl    = document.getElementById('fm-action-label');
        var listEl     = document.getElementById('fm-selected-files-list');
        if (!titleEl) return;

        var actionType = 'copy';
        var items = [];

        attachPathPicker(actionInp);

        function open(t) {
            items = getSelectedItems();
            if (!items.length) {
                toast('Sélectionnez au moins un élément.', 'warning');
                return;
            }
            if (t === 'rename' && items.length > 1) {
                toast('Renommer : sélectionnez un seul élément à la fois.', 'warning');
                return;
            }
            actionType = t;
            var cfg = {
                copy:   { title:'Copier',   btn:'Copier',   label:'Dossier destination :', val: getCurrentPath() },
                move:   { title:'Déplacer', btn:'Déplacer', label:'Dossier destination :', val: getCurrentPath() },
                rename: { title:'Renommer', btn:'Renommer', label:'Nouveau nom :',          val: items[0].name }
            };
            var c = cfg[t];
            titleEl.textContent    = c.title;
            confirmBtn.textContent = c.btn;
            labelEl.textContent    = c.label;
            actionInp.value        = c.val;
            actionInp.placeholder  = t === 'rename' ? 'ex: nouveau-nom.txt' : '/chemin/destination';
            listEl.innerHTML = items.map(itemHtml).join('');
            openOverlay(OVR);
            actionInp.focus();
            actionInp.select();
        }

        async function execute() {
            var val = actionInp.value.trim();
            if (!val) { toast('Champ requis.', 'warning'); actionInp.focus(); return; }
            setLoading(confirmBtn, true);
            try {
                var result;
                if (actionType === 'rename') {
                    if (val.includes('/')) { toast('Le nouveau nom ne doit pas contenir de "/".', 'error'); setLoading(confirmBtn,false); return; }
                    result = await apiCall({ operation:'rename', path: items[0].path, new_name: val });
                } else {
                    var sources = items.map(function(i) { return i.path; }).join('|');
                    result = await apiCall({ operation: actionType, sources: sources, destination: val });
                }
                if (result.error) { toast(result.error, 'error'); }
                else {
                    var labels = { copy:'Copié', move:'Déplacé', rename:'Renommé' };
                    toast((labels[actionType] || 'OK') + ' avec succès.', 'success');
                    closeOverlay(OVR);
                    refreshFolder();
                }
            } catch(e) { toast('Erreur : ' + e.message, 'error'); }
            finally    { setLoading(confirmBtn, false); }
        }

        var copyBtn   = document.querySelector('[data-action="copy"]');
        var moveBtn   = document.querySelector('[data-action="move"]');
        var renameBtn = document.querySelector('[data-action="rename"]');
        if (copyBtn)   copyBtn.addEventListener('click',   function(e) { e.preventDefault(); open('copy'); });
        if (moveBtn)   moveBtn.addEventListener('click',   function(e) { e.preventDefault(); open('move'); });
        if (renameBtn) renameBtn.addEventListener('click', function(e) { e.preventDefault(); open('rename'); });
        if (confirmBtn) confirmBtn.addEventListener('click', execute);
        if (cancelBtn)  cancelBtn.addEventListener('click',  function() { closeOverlay(OVR); });
        if (closeBtn)   closeBtn.addEventListener('click',   function() { closeOverlay(OVR); });
        if (actionInp)  actionInp.addEventListener('keydown', function(e) { if (e.key === 'Enter') execute(); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && isOpen(OVR)) closeOverlay(OVR); });
    })();

    // ══════════════════════════════════════════════════════════
    // MODAL 3 — PERMISSIONS
    // ══════════════════════════════════════════════════════════

    (function() {
        var OVR        = 'fm-permissions-modal-overlay';
        var confirmBtn = document.getElementById('fm-permissions-modal-confirm');
        var cancelBtn  = document.getElementById('fm-permissions-modal-cancel');
        var closeBtn   = document.getElementById('fm-permissions-modal-close');
        var listEl     = document.getElementById('fm-permissions-selected-list');
        var numInp     = document.getElementById('fm-permissions-numeric');
        if (!confirmBtn) return;

        var CB_IDS = [
            'perm-owner-read','perm-owner-write','perm-owner-execute',
            'perm-group-read','perm-group-write','perm-group-execute',
            'perm-other-read','perm-other-write','perm-other-execute'
        ];
        var targetItem = null;

        function calcNum() {
            function c(id) { var el = document.getElementById(id); return el ? el.checked : false; }
            var o = (c('perm-owner-read')?4:0)+(c('perm-owner-write')?2:0)+(c('perm-owner-execute')?1:0);
            var g = (c('perm-group-read')?4:0)+(c('perm-group-write')?2:0)+(c('perm-group-execute')?1:0);
            var t = (c('perm-other-read')?4:0)+(c('perm-other-write')?2:0)+(c('perm-other-execute')?1:0);
            if (numInp) numInp.value = '' + o + g + t;
            var tots = document.querySelectorAll('.fm-permissions__total');
            if (tots[0]) tots[0].textContent = o;
            if (tots[1]) tots[1].textContent = g;
            if (tots[2]) tots[2].textContent = t;
        }

        function setFromNum(v) {
            v = String(v).padStart(3,'0');
            function setBits(pfx, digit) {
                var n = parseInt(digit) || 0;
                var r = document.getElementById('perm-'+pfx+'-read');
                var w = document.getElementById('perm-'+pfx+'-write');
                var x = document.getElementById('perm-'+pfx+'-execute');
                if (r) r.checked = !!(n&4);
                if (w) w.checked = !!(n&2);
                if (x) x.checked = !!(n&1);
            }
            setBits('owner', v[0]); setBits('group', v[1]); setBits('other', v[2]);
            calcNum();
        }

        function open() {
            var sel = getSelectedItems();
            if (!sel.length) { toast('Sélectionnez un élément.', 'warning'); return; }
            if (sel.length > 1) { toast('Permissions : un seul élément à la fois.', 'warning'); return; }
            targetItem = sel[0];
            // Lire les permissions depuis le <tr> sélectionné (checkbox cochée)
            var perm = '644';
            var selRow = document.querySelector('#fm-tbody .fm-row .fm-checkbox:checked');
            if (selRow) {
                var tr = selRow.closest('.fm-row');
                var permEl = tr && tr.querySelector('.fm-perm, .fm-cell--perm, [data-perm]');
                if (permEl) perm = permEl.textContent.trim() || '644';
            }
            listEl.innerHTML = itemHtml(targetItem);
            setFromNum(perm);
            openOverlay(OVR);
        }

        async function apply() {
            var mode = numInp ? numInp.value.trim() : '';
            if (!mode || !/^[0-7]{3}$/.test(mode)) { toast('Mode invalide (ex: 644).', 'error'); return; }
            if (!targetItem) return;
            setLoading(confirmBtn, true);
            try {
                var r = await apiCall({ operation:'chmod', path: targetItem.path, mode: mode });
                if (r.error) { toast(r.error, 'error'); }
                else { toast('Permissions ' + mode + ' appliquées.', 'success'); closeOverlay(OVR); refreshFolder(); }
            } catch(e) { toast('Erreur : ' + e.message, 'error'); }
            finally    { setLoading(confirmBtn, false); }
        }

        CB_IDS.forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.addEventListener('change', calcNum);
        });
        if (numInp) numInp.addEventListener('input', function() {
            if (/^[0-7]{3}$/.test(numInp.value)) setFromNum(numInp.value);
        });

        var permBtn = document.querySelector('[data-action="permissions"]');
        if (permBtn) permBtn.addEventListener('click', function(e) { e.preventDefault(); open(); });
        if (confirmBtn) confirmBtn.addEventListener('click', apply);
        if (cancelBtn)  cancelBtn.addEventListener('click',  function() { closeOverlay(OVR); });
        if (closeBtn)   closeBtn.addEventListener('click',   function() { closeOverlay(OVR); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && isOpen(OVR)) closeOverlay(OVR); });
    })();

    // ══════════════════════════════════════════════════════════
    // MODAL 4 — COMPRESS
    // ══════════════════════════════════════════════════════════

    (function() {
        var OVR        = 'fm-compress-modal-overlay';
        var confirmBtn = document.getElementById('fm-compress-modal-confirm');
        var cancelBtn  = document.getElementById('fm-compress-modal-cancel');
        var closeBtn   = document.getElementById('fm-compress-modal-close');
        var listEl     = document.getElementById('fm-compress-selected-list');
        var nameInp    = document.getElementById('fm-compress-name');
        var formatRads = document.querySelectorAll('input[name="archive-format"]');
        if (!confirmBtn) return;

        var items = [];

        function open() {
            items = getSelectedItems();
            if (!items.length) { toast('Sélectionnez au moins un élément.', 'warning'); return; }
            listEl.innerHTML = items.map(itemHtml).join('');
            var base = items.length === 1 ? items[0].name.replace(/\.[^.]+$/, '') : 'archive';
            if (nameInp) nameInp.value = base + '.zip';
            var zipRad = document.querySelector('input[name="archive-format"][value="zip"]');
            if (zipRad) zipRad.checked = true;
            openOverlay(OVR);
            if (nameInp) nameInp.focus();
        }

        async function compress() {
            var archiveName = nameInp ? nameInp.value.trim() : '';
            if (!archiveName) { toast("Entrez un nom d'archive.", 'warning'); return; }
            var fmt     = (document.querySelector('input[name="archive-format"]:checked') || {}).value || 'zip';
            var dest    = getCurrentPath().replace(/\/+$/, '') + '/' + archiveName;
            var sources = items.map(function(i) { return i.path; }).join('|');
            var incH    = (document.getElementById('compress-include-hidden') || {}).checked ? '1' : '0';
            var folSym  = (document.getElementById('compress-follow-symlinks') || {}).checked ? '1' : '0';
            setLoading(confirmBtn, true);
            try {
                var r = await apiCall({ operation:'compress', sources:sources, destination:dest, format:fmt, include_hidden:incH, follow_symlinks:folSym });
                if (r.error) { toast(r.error, 'error'); }
                else { toast('"' + archiveName + '" créé.', 'success'); closeOverlay(OVR); refreshFolder(); }
            } catch(e) { toast('Erreur : ' + e.message, 'error'); }
            finally    { setLoading(confirmBtn, false); }
        }

        formatRads.forEach(function(radio) {
            radio.addEventListener('change', function() {
                if (!nameInp) return;
                var base = nameInp.value.replace(/\.(zip|tar\.gz|tar|7z)$/i, '');
                nameInp.value = base + '.' + this.value;
            });
        });

        var compBtn = document.querySelector('[data-action="compress"]');
        if (compBtn) compBtn.addEventListener('click', function(e) { e.preventDefault(); open(); });
        if (confirmBtn) confirmBtn.addEventListener('click', compress);
        if (cancelBtn)  cancelBtn.addEventListener('click',  function() { closeOverlay(OVR); });
        if (closeBtn)   closeBtn.addEventListener('click',   function() { closeOverlay(OVR); });
        if (nameInp)    nameInp.addEventListener('keydown', function(e) { if (e.key === 'Enter') compress(); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && isOpen(OVR)) closeOverlay(OVR); });
    })();

    // ══════════════════════════════════════════════════════════
    // MODAL 5 — DELETE
    // ══════════════════════════════════════════════════════════

    (function() {
        var OVR        = 'fm-delete-modal-overlay';
        var confirmBtn = document.getElementById('fm-delete-modal-confirm');
        var cancelBtn  = document.getElementById('fm-delete-modal-cancel');
        var closeBtn   = document.getElementById('fm-delete-modal-close');
        var listEl     = document.getElementById('fm-delete-selected-list');
        var cbConfirm  = document.getElementById('delete-confirm');
        var cbPerm     = document.getElementById('delete-permanently');
        if (!confirmBtn) return;

        var items = [];

        function open() {
            items = getSelectedItems();
            if (!items.length) { toast('Sélectionnez au moins un élément.', 'warning'); return; }
            listEl.innerHTML = items.map(itemHtml).join('');
            if (cbConfirm) cbConfirm.checked = false;
            if (cbPerm)    cbPerm.checked    = false;
            openOverlay(OVR);
        }

        async function doDelete() {
            if (cbConfirm && !cbConfirm.checked) {
                toast('Cochez la case de confirmation.', 'warning');
                if (cbConfirm) cbConfirm.focus();
                return;
            }
            var paths = items.map(function(i) { return i.path; }).join('|');
            setLoading(confirmBtn, true);
            try {
                var r = await apiCall({ operation:'delete', paths: paths });
                if (r.error) { toast(r.error, 'error'); }
                else { toast(items.length + ' élément(s) supprimé(s).', 'success'); closeOverlay(OVR); refreshFolder(); }
            } catch(e) { toast('Erreur : ' + e.message, 'error'); }
            finally    { setLoading(confirmBtn, false); }
        }

        var delBtn = document.querySelector('[data-action="delete"]');
        if (delBtn) delBtn.addEventListener('click', function(e) { e.preventDefault(); open(); });
        if (confirmBtn) confirmBtn.addEventListener('click', doDelete);
        if (cancelBtn)  cancelBtn.addEventListener('click',  function() { closeOverlay(OVR); });
        if (closeBtn)   closeBtn.addEventListener('click',   function() { closeOverlay(OVR); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && isOpen(OVR)) closeOverlay(OVR); });
    })();

    // ══════════════════════════════════════════════════════════
    // SYNC currentPath → fm-item-path
    // ══════════════════════════════════════════════════════════

    setInterval(function() {
        var p = document.getElementById('fm-item-path');
        if (p && !isOpen('fm-modal-overlay')) {
            var cp = getCurrentPath();
            if (p.value !== cp) p.value = cp;
        }
    }, 500);

})();

    // ══════════════════════════════════════════════════════════
    // BOUTON EDIT — ouvre l'éditeur dans un nouvel onglet
    // ══════════════════════════════════════════════════════════
    (function() {
        var editBtn = document.querySelector('[data-action="edit"]');
        if (!editBtn) return;
        editBtn.addEventListener('click', function(e) {
            e.preventDefault();
            var items = getSelectedItems();
            if (!items.length) { toast('Sélectionnez un fichier.', 'warning'); return; }
            var item = items[0];
            if (item.type === 'folder') { toast('Impossible d\'éditer un dossier.', 'warning'); return; }
            window.open('/edit/?path=' + encodeURIComponent(item.path), '_blank');
        });
    })();