#!/usr/bin/env python3
"""Serveur web — Page de lancement vérification QC (version déploiement).

Variables d'environnement :
  ACCESS_CODE   Code d'accès (défaut: wenov)
  FLASK_SECRET  Clé de signature des sessions (à définir en prod !)
  PORT          Port d'écoute (défaut: 5057)
"""
import json, os, uuid, time, secrets
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, session, redirect
from functools import wraps
from urllib.parse import quote

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-a-changer-en-prod')
ACCESS_CODE = os.environ.get('ACCESS_CODE', 'wenov')

# --- OAuth2 Adobe (Frame.io v4) ---
ADOBE_CLIENT_ID = os.environ.get('ADOBE_CLIENT_ID', '0eeaa9bf24224fefa381ce97784f7fb3')
ADOBE_CLIENT_SECRET = os.environ.get('ADOBE_CLIENT_SECRET', '')
OAUTH_REDIRECT_URI = os.environ.get(
    'OAUTH_REDIRECT_URI',
    'https://factory-qc-4olu.onrender.com/oauth/callback')
OAUTH_SCOPE = 'AdobeID,openid,email,profile,offline_access,additional_info.roles'

ESTIMATION_DEFAUT = {
    'design': {'par_fichier': 45, 'fixe': 20},
    'video':  {'par_fichier': 240, 'fixe': 30},
    'motion': {'par_fichier': 240, 'fixe': 30},
}

def load_clients():
    with open(os.path.join(BASE, 'clients.json')) as f:
        return json.load(f)

def charger_stats():
    p = os.path.join(BASE, 'stats.json')
    try:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def estimer_duree(type_job, nb_fichiers=2):
    stats = charger_stats()
    e = stats.get(type_job, {})
    par_fichier = e.get('par_fichier', ESTIMATION_DEFAUT[type_job]['par_fichier'])
    fixe = ESTIMATION_DEFAUT[type_job]['fixe']
    return int(fixe + par_fichier * nb_fichiers)

def fmt_duree(sec):
    sec = int(sec or 0)
    if sec < 60:
        return f"{sec}s"
    m, s = divmod(sec, 60)
    if m < 60:
        return f"{m:02d}:{s:02d}"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}"

def auth_requise(f):
    @wraps(f)
    def deco(*a, **kw):
        if not session.get('qc_auth'):
            return jsonify({'ok': False, 'erreur': 'Non authentifié.'}), 401
        return f(*a, **kw)
    return deco

@app.route('/')
def index():
    clients = load_clients()
    return render_template('index.html', clients=clients)

@app.route('/api/code', methods=['POST'])
def verifier_code():
    """Vérifie le code d'accès côté serveur et ouvre une session signée."""
    data = request.get_json(force=True, silent=True) or {}
    saisie = (data.get('code') or '').strip().lower()
    if saisie and saisie == ACCESS_CODE.lower():
        session['qc_auth'] = True
        session.permanent = True
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'erreur': 'Code incorrect.'}), 403

@app.route('/api/session')
def check_session():
    return jsonify({'ok': True, 'auth': bool(session.get('qc_auth'))})

@app.route('/api/deconnexion', methods=['POST'])
def deconnexion():
    session.pop('qc_auth', None)
    return jsonify({'ok': True})

@app.route('/oauth/login')
def oauth_login():
    """Lance l'autorisation Adobe (protégé par le code d'accès). À visiter une fois."""
    if not session.get('qc_auth'):
        return redirect('/')
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    url = ('https://ims-na1.adobelogin.com/ims/authorize/v2'
           f'?client_id={ADOBE_CLIENT_ID}'
           f'&redirect_uri={quote(OAUTH_REDIRECT_URI, safe="")}'
           f'&scope={quote(OAUTH_SCOPE, safe="")}'
           f'&response_type=code&state={state}')
    return redirect(url)

@app.route('/oauth/callback')
def oauth_callback():
    """Échange le code contre les tokens. Affiche le refresh_token à copier dans Render."""
    import urllib.request, urllib.error, urllib.parse
    if request.args.get('state') != session.get('oauth_state'):
        return 'État OAuth invalide, recommencez via /oauth/login.', 400
    code = request.args.get('code')
    if not code:
        return f"Erreur Adobe : {request.args.get('error_description', request.args.get('error'))}", 400
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'client_id': ADOBE_CLIENT_ID,
        'client_secret': ADOBE_CLIENT_SECRET,
        'code': code,
        'redirect_uri': OAUTH_REDIRECT_URI,
    }).encode()
    req = urllib.request.Request('https://ims-na1.adobelogin.com/ims/token/v3',
                                 data=data, method='POST',
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return f"Échange de code échoué (HTTP {e.code}).", 400
    rt = resp.get('refresh_token', '')
    if rt:
        try:
            open(os.path.join(BASE, 'adobe_refresh_token.txt'), 'w').write(rt)
        except Exception:
            pass
    # Page simple affichant le refresh token à copier dans Render
    return (f"""<html><body style="font-family:sans-serif;max-width:700px;margin:40px auto">
        <h2>✅ Autorisation réussie</h2>
        <p>Copiez ce <b>refresh token</b> dans Render → Environment → <b>ADOBE_REFRESH_TOKEN</b> :</p>
        <textarea rows="4" style="width:100%" readonly>{rt}</textarea>
        <p>Le worker l'utilisera pour obtenir des access tokens Frame.io v4.</p>
        </body></html>""")

def fmt_tc(sec):
    try:
        sec = int(sec or 0)
        return f"{sec // 60:02d}:{sec % 60:02d}"
    except Exception:
        return "??:??"

@app.route('/api/lancer', methods=['POST'])
@auth_requise
def lancer():
    data = request.get_json(force=True)
    client = data.get('client', '').strip()
    frameio_url = data.get('frameio_url', '').strip()
    type_livrable = data.get('type', '').strip()

    if not frameio_url:
        return jsonify({'ok': False, 'erreur': 'URL Frame.io manquante.'}), 400
    if type_livrable not in ('design', 'video', 'motion'):
        return jsonify({'ok': False, 'erreur': 'Type de livrable invalide.'}), 400

    clients = load_clients()
    dossier_trouve = None
    note_dossier = None
    # La page HTML n'a jamais de brief : toujours le mode B des règles.
    # Les règles Drive client + branding s'appliquent dès qu'un client est identifié.
    mode = 'sans_brief'
    if client and client != '__autre__':
        match = next((c for c in clients if c['name'] == client), None)
        if match and match.get('id'):
            dossier_trouve = match['id']
        else:
            note_dossier = ('Pas de dossier trouvé pour ce client — règles client et branding : '
                            'non applicables. Brief : non applicable (dépôt page HTML).')
    elif client == '__autre__':
        note_dossier = ('Pas de dossier trouvé (nouveau client) — règles client et branding : '
                        'non applicables. Brief : non applicable (dépôt page HTML).')
    else:
        # Dépôt rapide : lien seul, sans client ni brief
        client = 'Dépôt direct (sans client)'
        note_dossier = ('Mode sans brief : contrôle technique + langue + règles globales. '
                        'Brief, règles client et branding client : non applicables.')

    job = {
        'id': uuid.uuid4().hex[:12],
        'client': client if client != '__autre__' else 'Autre (nouveau)',
        'client_id': client,
        'dossier_drive': dossier_trouve,
        'note_dossier': note_dossier,
        'mode': mode,
        'frameio_url': frameio_url,
        'type': type_livrable,
        'charge': 'lourd' if type_livrable in ('video', 'motion') else 'leger',
        'statut': 'en_attente',
        'cree_le': datetime.now().isoformat(),
        'estimation_sec': estimer_duree(type_livrable),
        'progression': {'phase': 'attente', 'pourcent': 0},
    }
    qpath = os.path.join(BASE, 'queue', f"{job['id']}.json")
    with open(qpath, 'w') as f:
        json.dump(job, f, ensure_ascii=False, indent=2)

    return jsonify({'ok': True, 'job_id': job['id'],
                    'note_dossier': note_dossier,
                    'estimation': fmt_duree(job['estimation_sec'])})

def lire_job(qpath):
    with open(qpath) as f:
        return json.load(f)

@app.route('/api/statut/<job_id>')
def statut(job_id):
    qpath = os.path.join(BASE, 'queue', f'{job_id}.json')
    rpath = os.path.join(BASE, 'results', f'{job_id}.json')
    if os.path.exists(rpath):
        with open(rpath) as f:
            res = json.load(f)
        return jsonify({'ok': True, 'termine': True, 'resultat': res})
    if os.path.exists(qpath):
        job = lire_job(qpath)
        prog = job.get('progression', {})
        ecoule = 0
        try:
            debut = job.get('debut') or job.get('cree_le')
            ecoule = int(time.time() - datetime.fromisoformat(debut).timestamp())
        except Exception:
            pass
        estimation = prog.get('estimation_sec') or job.get('estimation_sec', 0)
        return jsonify({
            'ok': True, 'termine': False,
            'statut': job.get('statut', 'en_attente'),
            'phase': prog.get('phase', 'attente'),
            'pourcent': prog.get('pourcent', 0),
            'fichiers_faits': prog.get('fichiers_faits', 0),
            'fichiers_total': prog.get('fichiers_total', 0),
            'fichier_courant': prog.get('fichier_courant', ''),
            'ecoule_sec': ecoule,
            'ecoule': fmt_duree(ecoule),
            'estimation_sec': estimation,
            'estimation': fmt_duree(estimation),
            'restant_sec': max(0, estimation - ecoule),
            'restant': fmt_duree(max(0, estimation - ecoule)),
        })
    return jsonify({'ok': False, 'erreur': 'Job introuvable.'}), 404

@app.route('/api/jobs')
def jobs():
    actifs, termines = [], []
    qdir = os.path.join(BASE, 'queue')
    rdir = os.path.join(BASE, 'results')

    attente_tries = []
    for fn in os.listdir(qdir):
        if fn.endswith('.json'):
            try:
                j = lire_job(os.path.join(qdir, fn))
                if j.get('statut') == 'en_attente':
                    attente_tries.append(j)
            except Exception:
                pass
    attente_tries.sort(key=lambda j: j.get('cree_le', ''))
    positions = {j['id']: i + 1 for i, j in enumerate(attente_tries)}

    for fn in sorted(os.listdir(qdir), reverse=True):
        if not fn.endswith('.json'):
            continue
        try:
            j = lire_job(os.path.join(qdir, fn))
        except Exception:
            continue
        rid = fn[:-5]
        if os.path.exists(os.path.join(rdir, f'{rid}.json')):
            continue
        prog = j.get('progression', {})
        ecoule = 0
        try:
            debut = j.get('debut') or j.get('cree_le')
            ecoule = int(time.time() - datetime.fromisoformat(debut).timestamp())
        except Exception:
            pass
        estimation = prog.get('estimation_sec') or j.get('estimation_sec', 0)
        actifs.append({
            'id': j['id'], 'client': j['client'], 'type': j['type'],
            'charge': j.get('charge', 'leger'),
            'frameio_url': j['frameio_url'],
            'cree_le': j['cree_le'],
            'statut': j.get('statut', 'en_attente'),
            'phase': prog.get('phase', 'attente'),
            'pourcent': prog.get('pourcent', 0),
            'fichiers_faits': prog.get('fichiers_faits', 0),
            'fichiers_total': prog.get('fichiers_total', 0),
            'fichier_courant': prog.get('fichier_courant', ''),
            'ecoule': fmt_duree(ecoule),
            'estimation': fmt_duree(estimation),
            'restant': fmt_duree(max(0, estimation - ecoule)),
            'position_file': positions.get(j['id'], 0),
        })

    for fn in sorted(os.listdir(rdir), reverse=True)[:30]:
        if not fn.endswith('.json') or fn.endswith('-rapport.md'):
            continue
        try:
            with open(os.path.join(rdir, fn)) as f:
                r = json.load(f)
        except Exception:
            continue
        # Commentaires publiés, à plat pour affichage direct dans la page
        commentaires = []
        for fich in r.get('fichiers', []):
            for c in fich.get('commentaires', []):
                sec = c.get('timestamp', 0) if isinstance(c, dict) else 0
                txt = c.get('text', '') if isinstance(c, dict) else str(c)
                commentaires.append({
                    'fichier': fich.get('name', ''),
                    'tc': fmt_tc(sec),
                    'text': txt,
                })
        termines.append({
            'id': r.get('job_id', fn[:-5]),
            'client': r.get('client', '?'),
            'type': r.get('type', '?'),
            'mode': r.get('mode', 'avec_brief'),
            'frameio_url': r.get('frameio_url', ''),
            'termine_le': r.get('termine_le', ''),
            'duree': fmt_duree(r.get('duree_sec', 0)),
            'fichiers_traites': r.get('fichiers_traites', 0),
            'commentaires_publies': r.get('commentaires_publies', 0),
            'commentaires': commentaires,
            'rapport': r.get('rapport', ''),
        })

    return jsonify({'ok': True, 'actifs': actifs, 'termines': termines})

@app.route('/api/rapport/<job_id>')
def rapport(job_id):
    rpath = os.path.join(BASE, 'results', f'{job_id}-rapport.md')
    if os.path.exists(rpath):
        with open(rpath) as f:
            return Response(f.read(), mimetype='text/markdown; charset=utf-8')
    return jsonify({'ok': False, 'erreur': 'Rapport introuvable.'}), 404

@app.route('/api/rapports-drive')
@auth_requise
def rapports_drive():
    """Rapports sauvegardés dans Google Drive (survit aux redémarrages)."""
    try:
        import sys
        sys.path.insert(0, BASE)
        from drive_store import lister_rapports
        return jsonify({'ok': True, 'rapports': lister_rapports()})
    except Exception:
        return jsonify({'ok': True, 'rapports': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5057))
    app.run(host='0.0.0.0', port=port)
