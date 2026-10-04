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

def charge_job(job):
    return 'lourd' if job.get('type') in ('video', 'motion') else 'leger'

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
    l'ID de l'asset visualisé dans le meta og:image :
    .../image/<asset_id>/image_full_...
    """
    import urllib.request, urllib.error
    m = re.search(r'f\.io/([A-Za-z0-9_-]+)', url)
    if not m:
        m = re.search(r'frame\.io/.*[/-]([a-f0-9-]{36})', url)
        if m:
            return None, [{'id': m.group(1)}]
        return None, []
    share_code = m.group(1)
    # Retry sur échec réseau transitoire
    html = ''
    final_url = ''
    captured = [share_code]
    succes = False
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

            req = urllib.request.Request(f"https://f.io/{share_code}",
                                         headers={"User-Agent": "Mozilla/5.0"})
            opener = urllib.request.build_opener(CaptureRedirect)
            try:
                with opener.open(req, timeout=20) as r:
                    final_url = r.geturl()
                    html = r.read().decode('utf-8', errors='ignore')
            except urllib.error.HTTPError as e:
                print(f"resolve_share HTTP {e.code}", flush=True)
                return share_code, []
            except Exception as e:
                partial = getattr(e, 'partial', b'')
                if partial:
                    html = partial.decode('utf-8', errors='ignore')
                else:
                    raise
            succes = True
            break
        except Exception as e:
            if tentative < 2:
                print(f"resolve_share tentative {tentative+1}/3: {e}", flush=True)
                time.sleep(2)
            else:
                print(f"resolve_share échec définitif: {e}", flush=True)
                return share_code, []
    if not succes:
        return share_code, []
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

# --- Règles Drive ---
def lire_regles():
    regles = {}
    for fn in sorted(REGLES.glob('*.md')):
        try:
            regles[fn.stem] = fn.read_text()
        except Exception:
            pass
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
model = WhisperModel(WHISPER_MODEL, device='cpu', compute_type='int8')
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

    if ftype in ('video', 'motion'):
        etape('transcription')
        wav = workdir / f"{fid}.wav"
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

    return result

# --- Traitement d'un job complet ---
def traiter_job(job):
    jid = job['id']
    debut = time.time()
    print(f"[{jid}] {job['client']} | {job['type']} | {job['frameio_url']}", flush=True)

    job['statut'] = 'en_cours'
    job['debut'] = datetime.now().isoformat()
    if 'progression' not in job:
        job['progression'] = {}
    job['progression']['estimation_sec'] = job.get('estimation_sec') or estimer_duree(job['type'])
    job['progression']['phase'] = 'resolution'
    job['progression']['pourcent'] = 2
    (QUEUE / f"{jid}.json").write_text(json.dumps(job, ensure_ascii=False, indent=2))

    regles = lire_regles()
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

    # Affiner l'estimation avec le vrai nombre de fichiers
    if files:
        maj_progression(jid, fichiers_total=len(files),
                        estimation_sec=estimer_duree(job['type'], len(files)))

    resultat = {
        'job_id': jid,
        'client': job['client'],
        'type': job['type'],
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
    lignes = [f"# Rapport de vérification — {job['client']}",
              f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
              f"Type : {job['type']} | Lien : {job['frameio_url']}"]
    if job.get('note_dossier'):
        lignes.append(f"> ⚠️ {job['note_dossier']}")
    lignes += [f"\n## Fichiers traités : {resultat['fichiers_traites']}",
               f"## Commentaires publiés : {resultat['commentaires_publies']}\n"]
    for fr in resultat['fichiers']:
        lignes.append(f"### {fr.get('name', fr['file_id'])}")
        # Fiche technique
        if fr.get('technique'):
            lignes.append("**Contrôle technique :**")
            for t in fr['technique']:
                lignes.append(f"- {t}")
        for c in fr.get('commentaires', []):
            txt = c.get('text', '') if isinstance(c, dict) else str(c)
            lignes.append(f"- 💬 {txt}")
        for e in fr.get('erreurs', []):
            lignes.append(f"- ❌ {e}")
        if fr.get('note'):
            lignes.append(f"- ℹ️ {fr['note']}")
    rapport_path.write_text('\n'.join(lignes), encoding='utf-8')
    resultat['rapport'] = f"/api/rapport/{jid}"

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
