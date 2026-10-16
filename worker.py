#!/usr/bin/env python3
"""Worker — traite la file de vérifications QC avec ordonnancement intelligent.

Stratégie d'ordonnancement (optimisée vitesse + précision) :
- Les jobs VIDÉO/MOTION sont lourds (transcription Whisper + OCR sur CPU).
  Sur une machine à 2 cœurs, les lancer en parallèle ralentirait tout le monde
  et augmenterait le risque d'erreurs/timeouts → 1 seul à la fois.
- Les jobs DESIGN sont légers (téléchargement + analyse image, surtout I/O).
  Ils peuvent tourner en parallèle sans impacter la précision → jusqu'à 2.
- Un design ne reste jamais bloqué derrière une vidéo si un slot léger est libre
  (file express), sauf si une vidéo attend depuis plus de 10 min (anti-famine).

Chaque job suit sa progression (phase, fichiers, temps écoulé/estimé) dans son
fichier queue/<id>.json, lue par la page web pour la jauge.
"""
import json, os, sys, time, subprocess, re, shutil, threading
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
QUEUE = BASE / 'queue'
RESULTS = BASE / 'results'
REGLES = BASE / 'regles'
# Modèle Whisper : nom faster-whisper (téléchargé si absent) ou chemin local
WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'small')
STATS_PATH = BASE / 'stats.json'

# --- Configuration d'ordonnancement ---
MAX_LOURD_PARALLELE = 1   # vidéo/motion : CPU-bound → séquentiel
MAX_LEGER_PARALLELE = 2   # design : I/O-bound → parallèle limité
ANTI_FAMINE_SEC = 600     # après 10 min d'attente, un lourd devient prioritaire

sem_lourd = threading.Semaphore(MAX_LOURD_PARALLELE)
sem_leger = threading.Semaphore(MAX_LEGER_PARALLELE)
verrou = threading.Lock()
actifs = {}  # job_id -> {'thread': t, 'charge': 'lourd'|'leger', 'sem': sem}

# --- Estimations de durée (secondes) ---
# Affinées automatiquement via stats.json (moyenne mobile des durées réelles).
ESTIMATION_DEFAUT = {
    'design': {'par_fichier': 45, 'fixe': 20},
    'video':  {'par_fichier': 240, 'fixe': 30},   # transcription CPU ~4 min/fichier
    'motion':  {'par_fichier': 240, 'fixe': 30},
}

def charger_stats():
    try:
        if STATS_PATH.exists():
            return json.loads(STATS_PATH.read_text())
    except Exception:
        pass
    return {}

def enregistrer_stat(type_job, duree_sec, nb_fichiers):
    """Moyenne mobile exponentielle des durées réelles par type."""
    try:
        stats = charger_stats()
        e = stats.get(type_job, {})
        alpha = 0.3
        ancien_par_fichier = e.get('par_fichier', ESTIMATION_DEFAUT[type_job]['par_fichier'])
        nouveau = duree_sec / max(nb_fichiers, 1)
        e['par_fichier'] = round(alpha * nouveau + (1 - alpha) * ancien_par_fichier)
        e['echantillons'] = e.get('echantillons', 0) + 1
        e['maj'] = datetime.now().isoformat()[:16]
        stats[type_job] = e
        STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    except Exception as ex:
        print(f"Stats: {ex}", flush=True)

def estimer_duree(type_job, nb_fichiers=2):
    stats = charger_stats()
    e = stats.get(type_job, {})
    par_fichier = e.get('par_fichier', ESTIMATION_DEFAUT[type_job]['par_fichier'])
    fixe = ESTIMATION_DEFAUT[type_job]['fixe']
    return int(fixe + par_fichier * nb_fichiers)

def normaliser_pipeline(type_job):
    return 'video' if type_job == 'motion' else type_job

def charge_job(job):
    return 'lourd' if normaliser_pipeline(job.get('type')) == 'video' else 'leger'

# --- Frame.io ---
def frameio_token():
    """Token Frame.io v4 : OAuth2 Adobe (prod, via refresh token),
    ou FRAMEIO_TOKEN legacy (dev), ou credential local du runtime Muse."""
    try:
        sys.path.insert(0, str(BASE))
        from adobe_auth import get_access_token
        return get_access_token()
    except Exception as e:
        print(f"OAuth Adobe indisponible ({e}), repli legacy...", flush=True)
    tok = os.environ.get('FRAMEIO_TOKEN', '').strip()
    if tok:
        return tok
    try:
        sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
        from dynamic_credentials import dynamic_credential_entry
        entry = dynamic_credential_entry("custom.frameio-oauth", "access_token")
        return str(entry["surrogate"]).strip()
    except Exception:
        raise RuntimeError("Aucun token Frame.io : configurer ADOBE_REFRESH_TOKEN (prod) ou FRAMEIO_TOKEN.")

ACCT = os.environ.get('FRAMEIO_ACCOUNT_ID', '4516c658-53a4-4a52-8b5a-d200803ed2d6')

def api(method, path, data=None):
    import urllib.request, urllib.error
    token = frameio_token()
    url = f"https://api.frame.io{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("api-version", "experimental")
    req.add_header("User-Agent", "Mozilla/5.0")
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=body, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]

def resolve_share(url):
    """Résout un lien f.io -> (share_id, asset_id).

    https://f.io/XXXX redirige vers la page du partage. Le HTML contient
    l'ID de l'asset visualisé dans les URLs /image/<asset_id>/...

    Note : f.io / next.frame.io ont une protection anti-robot qui peut
    refuser les requêtes serveur (HTTP 403). On utilise des en-têtes
    navigateur complets + 3 tentatives avant d'abandonner avec un
    message explicite.
    """
    import urllib.request, urllib.error
    m = re.search(r'f\.io/([A-Za-z0-9_-]+)', url)
    if not m:
        m = re.search(r'frame\.io/.*[/-]([a-f0-9-]{36})', url)
        if m:
            return None, [{'id': m.group(1)}]
        return None, []
    share_code = m.group(1)
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }
    # Retry sur échec réseau OU HTTP (ex. 403 anti-robot) — jamais d'abandon immédiat
    html = ''
    final_url = ''
    captured = [share_code]
    succes = False
    derniere_erreur = ''
    for tentative in range(3):
        try:

            class CaptureRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    loc = newurl or headers.get('Location', '')
                    mm = re.search(r'/share/([a-f0-9-]{36})', loc)
                    if mm:
                        captured[0] = mm.group(1)
                    return urllib.request.HTTPRedirectHandler.redirect_request(
                        self, req, fp, code, msg, headers, newurl)

            req = urllib.request.Request(f"https://f.io/{share_code}", headers=HEADERS)
            opener = urllib.request.build_opener(CaptureRedirect)
            try:
                with opener.open(req, timeout=20) as r:
                    final_url = r.geturl()
                    html = r.read().decode('utf-8', errors='ignore')
            except urllib.error.HTTPError as e:
                derniere_erreur = f"HTTP {e.code}"
                print(f"resolve_share tentative {tentative+1}/3: HTTP {e.code}", flush=True)
                time.sleep(2 * (tentative + 1))
                continue
            except Exception as e:
                partial = getattr(e, 'partial', b'')
                if partial:
                    html = partial.decode('utf-8', errors='ignore')
                else:
                    derniere_erreur = str(e)[:120]
                    print(f"resolve_share tentative {tentative+1}/3: {e}", flush=True)
                    time.sleep(2 * (tentative + 1))
                    continue
            succes = True
            break
        except Exception as e:
            derniere_erreur = str(e)[:120]
            print(f"resolve_share tentative {tentative+1}/3: {e}", flush=True)
            time.sleep(2 * (tentative + 1))
    if not succes:
        raise RuntimeError(
            f"Lien Frame.io injoignable après 3 essais ({derniere_erreur or 'échec réseau'}). "
            "Astuce : ouvrez le lien dans votre navigateur, cliquez sur la vidéo, "
            "puis collez l'URL complète (elle contient /view/...)."
        )
    share_id = captured[0]
    # Tous les assets du partage via les URLs d'images /image/<uuid>/
    # (chaque vidéo du partage a sa miniature). Dédupliqué.
    vus = set()
    assets = []
    for m2 in re.finditer(r'/image/([a-f0-9-]{36})/', html):
        aid = m2.group(1)
        if aid not in vus:
            vus.add(aid)
            assets.append({'id': aid})
    # Partages multi-assets : la page est une SPA React ; les assets ne sont
    # pas dans le HTML statique mais dans le cache Apollo embarqué
    # ("InboxItemAsset:<uuid>"). Ces IDs sont les file IDs v4 (vérifié :
    # même namespace que l'asset téléchargé via /v4/files). On privilégie
    # les assets de type FILE (pas les dossiers partagés).
    unesc = html.replace('\\"','"')
    for m2 in re.finditer(
            r'InboxItemAsset:([a-f0-9-]{36})[^{]*?"assetType":"FILE"', unesc):
        aid = m2.group(1)
        if aid not in vus:
            vus.add(aid)
            assets.append({'id': aid})
    for m2 in re.finditer(r'InboxItemAsset:([a-f0-9-]{36})', unesc):
        aid = m2.group(1)
        if aid not in vus:
            vus.add(aid)
            assets.append({'id': aid})
    if assets:
        return share_id, assets
    # Repli : asset dans l'URL finale
    m2 = re.search(r'/view/([a-f0-9-]{36})', final_url)
    if m2:
        return share_id, [{'id': m2.group(1)}]
    return share_id, []

def get_file_info(file_id):
    code, data = api('GET', f'/v4/accounts/{ACCT}/files/{file_id}')
    if code == 200:
        d = data.get('data', data)
        return {'id': file_id, 'name': d.get('name', file_id),
                'type': d.get('type', ''), 'duration': d.get('duration')}
    return {'id': file_id, 'name': file_id, 'type': '', 'duration': None}

def get_hq_url(file_id):
    code, data = api('GET', f'/v4/accounts/{ACCT}/files/{file_id}?include=media_links.high_quality')
    if code == 200:
        d = data.get('data', data)
        ml = d.get('media_links', {})
        hq = ml.get('high_quality', {})
        return hq.get('download_url')
    return None

def post_comment(file_id, seconds, text, fps=30):
    ts = int(seconds * fps)
    code, data = api('POST', f'/v4/accounts/{ACCT}/files/{file_id}/comments',
                     {"data": {"text": text, "timestamp": ts}})
    return code in (200, 201)

def compter_commentaires(fid):
    """Nombre de commentaires persistés sur Frame.io (F-012 : la source de
    vérité est GET /comments, pas le compteur du worker). Suit la pagination.
    None si injoignable."""
    try:
        total, url = 0, f'/v4/accounts/{ACCT}/files/{fid}/comments'
        for _ in range(20):  # garde-fou : 20 pages max
            c, d = api('GET', url)
            if c != 200 or not isinstance(d, dict):
                return None
            total += len(d.get('data', []))
            nxt = (d.get('links') or {}).get('next')
            if not nxt:
                return total
            url = nxt if nxt.startswith('/v4/') else '/v4/' + nxt.lstrip('/')
        return total
    except Exception:
        pass
    return None

# --- Règles (factory v3 : un paquet par pipeline) ---
# DESIGN -> REGLES_COMMUNES + REGLES_DESIGN
# VIDÉO  -> REGLES_COMMUNES + REGLES_VIDEO
# 'motion' (anciens jobs) est traité comme 'video'.
REGLES_PAR_PIPELINE = {
    'design': ['00_LIRE_EN_PREMIER.md', 'REGLES_COMMUNES.md', 'REGLES_DESIGN.md'],
    'video': ['00_LIRE_EN_PREMIER.md', 'REGLES_COMMUNES.md', 'REGLES_VIDEO.md'],
}

def lire_regles(pipeline):
    """Charge le paquet de règles du pipeline (dossier regles du déploiement)."""
    pipeline = normaliser_pipeline(pipeline)
    fichiers = REGLES_PAR_PIPELINE.get(pipeline, REGLES_PAR_PIPELINE['video'])
    regles = {}
    for fn in fichiers:
        p = REGLES / fn
        try:
            regles[fn] = p.read_text()
        except Exception as e:
            regles[fn] = f"[ERREUR LECTURE: {e}]"
    return regles

# --- Transcription ---
def transcrire(video_path, wav_path):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(video_path),
                    '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le',
                    str(wav_path)], check=True, timeout=300)
    venv_py = sys.executable
    script = f"""
import json, numpy as np, soundfile as sf
from faster_whisper import WhisperModel
model = WhisperModel('{WHISPER_MODEL}', device='cpu', compute_type='int8')
audio, sr = sf.read('{wav_path}')
segments, info = model.transcribe(audio, language='fr', beam_size=5)
segs = [{{'start': s.start, 'end': s.end, 'text': s.text.strip()}} for s in segments]
print(json.dumps({{'segments': segs, 'lang': info.language}}))
"""
    p = subprocess.run([str(venv_py), '-c', script], capture_output=True,
                       text=True, timeout=1800)
    m = re.search(r'\{"segments".*\}', p.stdout, re.DOTALL)
    if not m:
        raise RuntimeError(f"Transcription échouée: {p.stderr[:300]}")
    return json.loads(m.group(0))

# --- Vérification linguistique (LANG-003..007, V-04/SUB-005) ---
LANGUAGETOOL_URL = 'https://api.languagetool.org/v2/check'

def formater_tc(sec):
    m, s = divmod(int(max(0, sec)), 60)
    return f"{m:02d}:{s:02d}"

def verifier_texte_languagetool(text, lang='fr'):
    """Fautes détectées par LanguageTool : [{'faute','correction','regle'}].
    [] si le service est injoignable (ne bloque jamais le job)."""
    import urllib.request, urllib.error, urllib.parse
    if not text or len(text.strip()) < 3:
        return []
    resp = None
    for tentative in range(3):
        try:
            data = urllib.parse.urlencode(
                {'text': text, 'language': lang}).encode()
            req = urllib.request.Request(
                LANGUAGETOOL_URL, data=data, method='POST',
                headers={'Content-Type': 'application/x-www-form-urlencoded',
                         'User-Agent': 'Mozilla/5.0 (FactoryQC)'})
            with urllib.request.urlopen(req, timeout=25) as r:
                resp = json.loads(r.read().decode())
            break
        except Exception as e:
            print(f"LanguageTool tentative {tentative+1}/3: {e}", flush=True)
            time.sleep(2 * (tentative + 1))
    if resp is None:
        return []
    fautes = []
    for m in resp.get('matches', []):
        o, l = m.get('offset', 0), m.get('length', 0)
        if o < 0 or l <= 0 or o + l > len(text):
            continue
        rep = (m.get('replacements') or [{}])[0].get('value', '')
        if rep and rep.lower() == text[o:o+l].lower():
            continue
        fautes.append({'faute': text[o:o+l], 'correction': rep,
                       'regle': (m.get('rule') or {}).get('id', '')})
    return fautes

def commentaire_faute(sec, faute, correction):
    tc = formater_tc(sec)
    if correction:
        return (sec, f"{tc} — Corriger '{faute}' en '{correction}'.")
    return (sec, f"{tc} — '{faute}' : à vérifier.")

def texte_ecran_valide(texte):
    """Filtre anti-bruit OCR (V-02) : le texte doit ressembler à du vrai
    texte affiché, pas à un fragment de logo ou de décor."""
    t = (texte or '').strip()
    if len(t) < 12:
        return False
    mots = t.split()
    if len(mots) < 3:
        return False
    lettres = sum(1 for c in t if c.isalpha() or c in " '’«»")
    if lettres / len(t) < 0.7:
        return False
    tl = t.lower()
    if tl.startswith(('http', 'www.')) or t.replace(' ', '').isdigit():
        return False
    return True

def segment_transcription_valide(texte):
    """Filtre anti-bruit transcription : Whisper produit parfois des fragments
    (interjections, bruits) — LanguageTool ne doit corriger que des phrases."""
    t = (texte or '').strip()
    if len(t) < 10:
        return False
    if len(t.split()) < 2:
        return False
    return True

def faute_valide(faute, correction):
    """Une correction n'est publiée/rapportée que si elle est assez
    substantielle pour ne pas être un fragment de bruit (OCR/Whisper).
    Les cas sans suggestion vont au rapport uniquement via 'à vérifier'."""
    f = (faute or '').strip()
    if not (correction or '').strip():
        return False
    # La faute doit contenir au moins 3 lettres consécutives
    if not re.search(r'[A-Za-zÀ-ÿ]{3,}', f):
        return False
    return True

def extraire_textes_ecran(video_path, workdir):
    """V-02/SUB-001 : 1 capture/seconde + OCR tesseract (fra+eng).
    Retourne [(sec, texte)] — un seul par texte distinct consécutif."""
    frames = workdir / 'frames'
    frames.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(video_path),
                    '-vf', 'fps=1,scale=1280:-1',
                    str(frames / 'f%04d.png')],
                   timeout=600, check=True)
    resultats, dernier = [], None
    for img in sorted(frames.glob('f*.png')):
        try:
            sec = int(img.stem[1:]) - 1
        except ValueError:
            continue
        try:
            p = subprocess.run(['tesseract', str(img), 'stdout', '-l', 'fra+eng',
                                '--psm', '6'],
                               capture_output=True, text=True, timeout=90)
            texte = ' '.join(p.stdout.split())
        except Exception:
            continue
        if texte == dernier:
            continue
        dernier = texte
        # V-02 : filtrer fragments (logos/URLs) et bruit OCR
        if len(texte) >= 4 and not texte.lower().startswith(('http', 'www.')):
            resultats.append((sec, texte))
    return resultats

# --- Progression ---
def maj_progression(jid, phase=None, fichiers_faits=None, fichiers_total=None,
                    estimation_sec=None, fichier_courant=None):
    """Met à jour le fichier du job avec la progression (lu par la page web)."""
    try:
        qp = QUEUE / f"{jid}.json"
        if not qp.exists():
            return
        job = json.loads(qp.read_text())
        prog = job.get('progression', {})
        if phase is not None:
            prog['phase'] = phase
        if fichiers_faits is not None:
            prog['fichiers_faits'] = fichiers_faits
        if fichiers_total is not None:
            prog['fichiers_total'] = fichiers_total
        if estimation_sec is not None:
            prog['estimation_sec'] = estimation_sec
        if fichier_courant is not None:
            prog['fichier_courant'] = fichier_courant
        # Pourcentage global
        ff = prog.get('fichiers_faits', 0)
        ft = prog.get('fichiers_total', 0)
        poids_phase = {'resolution': 5, 'telechargement': 15, 'transcription': 40,
                       'analyse': 65, 'traitement': 50,
                       'publication': 90, 'rapport': 97, 'termine': 100}
        base = poids_phase.get(prog.get('phase', ''), 0)
        if ft and ff is not None:
            # interpolation simple : phase + avancement fichiers dans la phase
            prog['pourcent'] = min(99, int(base * 0.5 + 50 * ff / max(ft, 1)))
        else:
            prog['pourcent'] = min(99, base)
        prog['maj'] = datetime.now().isoformat()
        job['progression'] = prog
        job['statut'] = 'en_cours'
        qp.write_text(json.dumps(job, ensure_ascii=False, indent=2))
    except Exception as ex:
        print(f"[{jid}] maj_progression: {ex}", flush=True)

# --- Traitement d'un fichier ---
def traiter_fichier(job, file_info, workdir, regles, jid=None, idx=0, total=1):
    fid = file_info['id']
    fname = file_info.get('name', fid)
    ftype = job['type']
    result = {'file_id': fid, 'name': fname, 'commentaires': [], 'erreurs': []}

    def etape(phase):
        if jid:
            maj_progression(jid, phase=phase, fichiers_faits=idx,
                            fichiers_total=total, fichier_courant=fname)

    etape('telechargement')
    hq_url = get_hq_url(fid)
    if not hq_url:
        result['erreurs'].append('URL de téléchargement introuvable')
        return result

    ext = '.mp4' if ftype in ('video', 'motion') else '.png'
    local = workdir / f"{fid}{ext}"
    subprocess.run(['curl', '-sL', '-o', str(local), hq_url], timeout=600)

    # Durée réelle (pour placer le « PARFAIT ! » en fin de vidéo)
    duree_video = file_info.get('duration') or 0
    if ftype == 'video' and not duree_video:
        try:
            p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                'format=duration', '-of', 'csv=p=0', str(local)],
                               capture_output=True, text=True, timeout=30)
            duree_video = float(p.stdout.strip())
        except Exception:
            duree_video = 0

    if ftype == 'video':
        etape('transcription')
        wav = workdir / f"{fid}.wav"
        tr = None
        try:
            tr = transcrire(local, wav)
            result['transcription_segments'] = len(tr['segments'])
            result['note'] = f"Transcription: {len(tr['segments'])} segments. Analyse détaillée dans le rapport."
            (workdir / f"{fid}-transcription.json").write_text(
                json.dumps(tr, ensure_ascii=False, indent=1))
        except Exception as e:
            result['erreurs'].append(f'Transcription: {e}')
        etape('analyse')
        # --- Contrôle technique (audio/vidéo) ---
        try:
            sys.path.insert(0, str(BASE))
            from controle_technique import verifier_technique
            tech = verifier_technique(local, wav_path=wav if wav.exists() else None)
            result['technique'] = tech['fiches']
            result['technique_sain'] = tech['sain']
            # Les alertes techniques deviennent des commentaires Frame.io
            # (secondes, texte) -> format commentaire
            for sec, txt in tech['commentaires']:
                result['commentaires'].append({'timestamp': sec, 'text': txt})
        except Exception as e:
            result['erreurs'].append(f'Contrôle technique: {e}')
        # --- Vérification linguistique unifiée (V-04/SUB-005, LANG-003..007) ---
        # Transcription (phrases réelles -> fiables) + OCR écran (filtré
        # anti-bruit). Déduplication globale, max 10 commentaires/fichier ;
        # le reste est consigné dans le rapport.
        try:
            vus = set()
            corrections = []  # [(sec, faute, correction)]
            if tr:
                for seg in tr.get('segments', []):
                    texte = (seg.get('text') or '').strip()
                    if not segment_transcription_valide(texte):
                        continue
                    sec = seg.get('start', 0) or 0
                    for f in verifier_texte_languagetool(texte, 'fr'):
                        if not faute_valide(f['faute'], f['correction']):
                            continue
                        cle = (f['faute'].lower(), f['correction'].lower())
                        if cle not in vus:
                            vus.add(cle)
                            corrections.append((sec, f['faute'], f['correction']))
                    time.sleep(0.3)
            ocr = extraire_textes_ecran(local, workdir)
            result['textes_ecran'] = [{'sec': s, 'texte': t} for s, t in ocr]
            for sec, texte in ocr:
                if not texte_ecran_valide(texte):
                    continue
                for f in verifier_texte_languagetool(texte, 'fr'):
                    if not faute_valide(f['faute'], f['correction']):
                        continue
                    cle = (f['faute'].lower(), f['correction'].lower())
                    if cle not in vus:
                        vus.add(cle)
                        corrections.append((sec, f['faute'], f['correction']))
                time.sleep(0.3)
            result['corrections_texte'] = [
                {'sec': s, 'faute': fa, 'correction': co}
                for s, fa, co in corrections]
            for sec, fa, co in corrections[:10]:
                s_, txt = commentaire_faute(sec, fa, co)
                result['commentaires'].append({'timestamp': s_, 'text': txt})
            if len(corrections) > 10:
                result['note'] = (result.get('note', '') +
                    f" {len(corrections) - 10} correction(s) linguistique(s) "
                    f"supplémentaire(s) dans le rapport.")
        except Exception as e:
            result['erreurs'].append(f'Verif linguistique: {e}')
    else:
        etape('analyse')
        try:
            p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                '-show_entries', 'stream=width,height',
                                '-of', 'json', str(local)],
                               capture_output=True, text=True, timeout=30)
            info = json.loads(p.stdout)
            s = info['streams'][0]
            result['dimensions'] = f"{s['width']}x{s['height']}"
        except Exception as e:
            result['erreurs'].append(f'Analyse image: {e}')
        # --- OCR + vérification linguistique du visuel (D-01/LANG) ---
        try:
            p = subprocess.run(['tesseract', str(local), 'stdout', '-l', 'fra+eng',
                                '--psm', '6'],
                               capture_output=True, text=True, timeout=120)
            texte = ' '.join(p.stdout.split())
            result['texte_detecte'] = texte
            for f in verifier_texte_languagetool(texte, 'fr'):
                if not faute_valide(f['faute'], f['correction']):
                    continue
                result['commentaires'].append(
                    {'timestamp': 0,
                     'text': f"Corriger '{f['faute']}' en '{f['correction']}'."})
                time.sleep(0.5)
        except Exception as e:
            result['erreurs'].append(f'OCR design: {e}')

    # REGLES_COMMUNES §4 : si tout est valide (aucun commentaire, aucune
    # erreur), publier un seul « PARFAIT ! » — placé à la fin de la vidéo
    # quand la durée est connue, sinon au début.
    if not result['commentaires'] and not result['erreurs']:
        try:
            ts = max(0.0, float(duree_video) - 1.0)
        except (TypeError, ValueError):
            ts = 0.0
        result['commentaires'].append({'timestamp': ts, 'text': 'PARFAIT !'})

    return result

# --- Traitement d'un job complet ---
def traiter_job(job):
    jid = job['id']
    debut = time.time()
    # Normaliser l'ancien type 'motion' -> 'video' (factory v3 : 2 pipelines)
    job['type'] = normaliser_pipeline(job.get('type', 'video'))
    print(f"[{jid}] {job['client']} | {job['type']} | {job['frameio_url']}", flush=True)

    job['statut'] = 'en_cours'
    job['debut'] = datetime.now().isoformat()
    if 'progression' not in job:
        job['progression'] = {}
    job['progression']['estimation_sec'] = job.get('estimation_sec') or estimer_duree(job['type'])
    job['progression']['phase'] = 'resolution'
    job['progression']['pourcent'] = 2
    (QUEUE / f"{jid}.json").write_text(json.dumps(job, ensure_ascii=False, indent=2))

    regles = lire_regles(job['type'])
    workdir = BASE / 'work' / jid
    workdir.mkdir(parents=True, exist_ok=True)

    # Résoudre le lien Frame.io -> les assets réellement partagés
    maj_progression(jid, phase='resolution')
    share_id, ids = resolve_share(job['frameio_url'])
    files = []
    # Chaque asset du partage -> infos via l'API (nom, etc.)
    for entry in ids[:20]:  # limite de sécurité
        fid = entry['id'] if isinstance(entry, dict) else entry
        files.append(get_file_info(fid))

    seen = set()
    uniq = []
    for f in files:
        if f['id'] not in seen:
            seen.add(f['id'])
            uniq.append(f)
    files = uniq

    # Résolution vide = échec, jamais un faux "terminé" (cf. job BBL 2026-10-03)
    if not files:
        raise RuntimeError(
            "Lien Frame.io inaccessible ou partage vide : 0 asset résolu "
            f"({job['frameio_url']})")

    # Affiner l'estimation avec le vrai nombre de fichiers
    if files:
        maj_progression(jid, fichiers_total=len(files),
                        estimation_sec=estimer_duree(job['type'], len(files)))

    resultat = {
        'job_id': jid,
        'client': job['client'],
        'type': job['type'],
        'pipeline': 'DESIGN' if job['type'] == 'design' else 'VIDÉO',
        'regles_appliquees': list(regles.keys()),
        'mode': job.get('mode', 'sans_brief'),
        'frameio_url': job['frameio_url'],
        'note_dossier': job.get('note_dossier'),
        'fichiers_traites': 0,
        'commentaires_publies': 0,
        'fichiers': [],
        'termine_le': datetime.now().isoformat(),
        'duree_sec': 0,
    }

    for i, fi in enumerate(files):
        try:
            fr = traiter_fichier(job, fi, workdir, regles, jid=jid,
                                 idx=i, total=len(files))
            # --- Publication des commentaires sur Frame.io ---
            maj_progression(jid, phase='publication', fichiers_faits=i,
                            fichiers_total=len(files),
                            fichier_courant=fi.get('name', ''))
            # F-012 : la source de vérité est GET /comments — compter
            # avant/après pour détecter un écart de persistance.
            avant = compter_commentaires(fi['id'])
            publies = 0
            for c in fr.get('commentaires', []):
                sec = c.get('timestamp', 0) if isinstance(c, dict) else 0
                txt = c.get('text', '') if isinstance(c, dict) else str(c)
                try:
                    if post_comment(fi['id'], sec, txt):
                        publies += 1
                    else:
                        fr.setdefault('commentaires_echecs', []).append(txt[:80])
                except Exception as e:
                    fr.setdefault('commentaires_echecs', []).append(
                        f"{txt[:60]}: {e}"[:100])
                time.sleep(1)  # éviter le rate-limit
            apres = compter_commentaires(fi['id'])
            if avant is not None and apres is not None and (apres - avant) != publies:
                fr.setdefault('erreurs', []).append(
                    f"Écart persistance commentaires : {publies} envoyé(s), "
                    f"{apres - avant} retrouvé(s) sur Frame.io.")
            fr['commentaires_publies_reel'] = publies
            resultat['fichiers'].append(fr)
            resultat['fichiers_traites'] += 1
            resultat['commentaires_publies'] += publies
        except Exception as e:
            resultat['fichiers'].append({
                'file_id': fi.get('id'), 'name': fi.get('name'),
                'erreurs': [str(e)[:200]]})
        maj_progression(jid, fichiers_faits=i + 1, fichiers_total=len(files))

    # Rapport
    maj_progression(jid, phase='rapport')
    rapport_path = RESULTS / f"{jid}-rapport.md"
    dossier = job.get('dossier_drive')
    lignes = [f"# Rapport de vérification — {job['client']}",
              f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
              f"Pipeline : {'DESIGN 🎨' if job['type'] == 'design' else 'VIDÉO 🎬'} | Lien : {job['frameio_url']}",
              f"Règles appliquées : {', '.join(regles.keys())}",
              f"Conformité au brief : non applicable — aucun brief fourni sur la page."]
    if dossier:
        lignes.append("> ℹ️ Règles Drive client et branding/visuels : vérifiés (dossier client).")
    else:
        lignes.append("> ⚠️ Règles client et branding client : non applicables (aucun dossier client). "
                      "Vérifié : règles globales du pipeline.")
    lignes += [f"\n## Fichiers traités : {resultat['fichiers_traites']}",
               f"## Commentaires publiés : {resultat['commentaires_publies']}\n"]
    for fr in resultat['fichiers']:
        lignes.append(f"### {fr.get('name', fr['file_id'])}")
        # Fiche technique
        if fr.get('technique'):
            lignes.append("**Contrôle technique :**")
            for t in fr['technique']:
                lignes.append(f"- {t}")
        # Vérification linguistique (V-04/SUB-005, LANG-003..007)
        if fr.get('corrections_texte'):
            lignes.append("**Corrections linguistiques :**")
            for co in fr['corrections_texte']:
                tc = f"{int(co['sec']) // 60:02d}:{int(co['sec']) % 60:02d}"
                lignes.append(f"- 🔤 {tc} — '{co['faute']}' → '{co['correction']}'")
        elif fr.get('transcription_segments'):
            lignes.append("- 🔤 Vérification linguistique : aucune faute détectée.")
        # Couverture OCR (V-02 : limite déclarée, jamais masquée)
        if fr.get('textes_ecran') is not None:
            lignes.append(f"- 📷 OCR : {len(fr['textes_ecran'])} texte(s) distinct(s) "
                          f"détecté(s) à 1 image/seconde. Limite : un élément affiché "
                          f"entre deux captures peut avoir été manqué.")
        for c in fr.get('commentaires', []):
            txt = c.get('text', '') if isinstance(c, dict) else str(c)
            lignes.append(f"- 💬 {txt}")
        for e in fr.get('erreurs', []):
            lignes.append(f"- ❌ {e}")
        if fr.get('note'):
            lignes.append(f"- ℹ️ {fr['note']}")
    rapport_path.write_text('\n'.join(lignes), encoding='utf-8')
    resultat['rapport'] = f"/api/rapport/{jid}"
    # --- Sauvegarde du rapport dans Google Drive (best-effort : ne fait
    # jamais échouer le job ; le Drive survit aux redémarrages Render) ---
    try:
        sys.path.insert(0, str(BASE))
        from drive_store import sauvegarder_rapport
        nom_drive = (f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_"
                     f"{re.sub(r'[^A-Za-z0-9_-]+', '_', job['client'])[:40]}_"
                     f"{job['type']}_{jid}.md")
        fid_drive, lien_drive = sauvegarder_rapport(rapport_path, nom_drive)
        if fid_drive:
            resultat['rapport_drive'] = lien_drive
    except Exception as e:
        print(f"[{jid}] sauvegarde Drive impossible : {e}", flush=True)

    duree = int(time.time() - debut)
    resultat['duree_sec'] = duree
    enregistrer_stat(job['type'], duree, max(resultat['fichiers_traites'], 1))

    (RESULTS / f"{jid}.json").write_text(
        json.dumps(resultat, ensure_ascii=False, indent=2))
    (QUEUE / f"{jid}.json").unlink(missing_ok=True)
    print(f"[{jid}] Terminé en {duree}s: {resultat['fichiers_traites']} fichiers, "
          f"{resultat['commentaires_publies']} commentaires", flush=True)

def executer_job(job, sem):
    """Point d'entrée du thread : exécute puis libère le slot."""
    try:
        traiter_job(job)
    except Exception as e:
        print(f"[{job['id']}] ERREUR FATALE: {e}", flush=True)
        try:
            qp = QUEUE / f"{job['id']}.json"
            if qp.exists():
                j = json.loads(qp.read_text())
                j['statut'] = 'erreur'
                j['erreur'] = str(e)[:300]
                qp.write_text(json.dumps(j, ensure_ascii=False, indent=2))
        except Exception:
            pass
    finally:
        sem.release()
        with verrou:
            actifs.pop(job['id'], None)

def charger_jobs_attente():
    out = []
    for jf in QUEUE.glob('*.json'):
        try:
            j = json.loads(jf.read_text())
            if j.get('statut') == 'en_attente':
                out.append(j)
        except Exception:
            pass
    # Tri : ancienneté d'abord, mais anti-famine pour les lourds
    now = time.time()
    def cle(j):
        try:
            cree = datetime.fromisoformat(j['cree_le']).timestamp()
        except Exception:
            cree = now
        attente = now - cree
        # Un lourd qui attend depuis > 10 min passe devant tout
        if charge_job(j) == 'lourd' and attente > ANTI_FAMINE_SEC:
            return (0, cree)
        return (1, cree)
    out.sort(key=cle)
    return out

def reprendre_jobs_abandonnes():
    """Au démarrage : tout job resté 'en_cours' (worker mort en plein traitement)
    repart en 'en_attente' au lieu de rester bloqué à jamais."""
    recuperes = []
    for jf in QUEUE.glob('*.json'):
        try:
            j = json.loads(jf.read_text())
            if j.get('statut') == 'en_cours':
                j['statut'] = 'en_attente'
                j['reprise_apres_crash'] = True
                jf.write_text(json.dumps(j, ensure_ascii=False, indent=2))
                recuperes.append(j['id'])
        except Exception:
            pass
    if recuperes:
        print(f"Reprise après crash : {len(recuperes)} job(s) remis en attente : "
              f"{', '.join(recuperes)}", flush=True)

def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    (BASE / 'work').mkdir(parents=True, exist_ok=True)
    reprendre_jobs_abandonnes()
    print(f"Worker QC démarré (lourd×{MAX_LOURD_PARALLELE}, léger×{MAX_LEGER_PARALLELE}).",
          flush=True)
    while True:
        try:
            with verrou:
                termines = [jid for jid, a in actifs.items()
                            if not a['thread'].is_alive()]
                for jid in termines:
                    actifs.pop(jid, None)

            for job in charger_jobs_attente():
                with verrou:
                    if job['id'] in actifs:
                        continue
                ch = charge_job(job)
                sem = sem_lourd if ch == 'lourd' else sem_leger
                if sem.acquire(blocking=False):
                    t = threading.Thread(target=executer_job,
                                         args=(job, sem), daemon=True,
                                         name=f"qc-{job['id']}")
                    with verrou:
                        actifs[job['id']] = {'thread': t, 'charge': ch, 'sem': sem}
                    # Marquer en_cours immédiatement pour éviter double prise
                    try:
                        qp = QUEUE / f"{job['id']}.json"
                        j = json.loads(qp.read_text())
                        if j.get('statut') == 'en_attente':
                            j['statut'] = 'en_cours'
                            qp.write_text(json.dumps(j, ensure_ascii=False, indent=2))
                    except Exception:
                        pass
                    t.start()
                    print(f"[{job['id']}] Démarré ({ch}) — "
                          f"actifs: {len(actifs)}", flush=True)
        except Exception as e:
            print(f"Boucle scheduler: {e}", flush=True)
        time.sleep(5)

if __name__ == '__main__':
    main()
