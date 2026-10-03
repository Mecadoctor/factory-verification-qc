#!/usr/bin/env python3
"""Contrôle technique vidéo — vérification qualité audio/vidéo.

Règles appliquées à chaque vidéo :
- VIDÉO : codec, résolution, fps, débit, durée
- AUDIO : codec, canaux (mono/stéréo), fréquence d'échantillonnage
- NIVEAUX : crêtes (dB), écrêtage, niveau trop faible
- SILENCES : détection des silences morts (> 3s)
- COHÉRENCE : alertes si mono au lieu de stéréo, etc.

Retourne :
- 'fiches' : liste de constats techniques (pour le rapport)
- 'commentaires' : liste de (secondes, texte) à publier sur Frame.io
- 'sain' : True si aucun problème bloquant
"""
import json, re, subprocess, sys
from pathlib import Path

# Ajouter le venv pour numpy/soundfile (analyse audio rapide)
_VENV = Path.home() / 'workspace' / 'qc-subs' / 'venv'
for _p in _VENV.glob('lib/python*/site-packages'):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def ffprobe_info(path):
    """Infos techniques via ffprobe."""
    p = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format',
         '-of', 'json', str(path)],
        capture_output=True, text=True, timeout=60)
    return json.loads(p.stdout)


def analyser_niveaux_wav(wav_path):
    """Crêtes et niveau moyen depuis le WAV (rapide, via numpy).

    Retourne {'max_db': ..., 'mean_db': ...} ou None si échec.
    """
    try:
        import numpy as np
        import soundfile as sf
        audio, sr = sf.read(str(wav_path))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)  # mixage mono pour la mesure
        # Éviter log(0)
        crete = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        max_db = 20 * np.log10(crete) if crete > 1e-10 else -96.0
        mean_db = 20 * np.log10(rms) if rms > 1e-10 else -96.0
        return {'max_db': round(float(max_db), 1),
                'mean_db': round(float(mean_db), 1)}
    except Exception:
        return None


def detecter_silences_wav(wav_path, seuil_db=-40, duree_min=3.0):
    """Silences morts depuis le WAV (fenêtres de 100ms)."""
    try:
        import numpy as np
        import soundfile as sf
        audio, sr = sf.read(str(wav_path))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        # Énergie par fenêtre de 100ms
        fen = int(sr * 0.1)
        n = len(audio) // fen
        if n == 0:
            return []
        tronque = audio[:n * fen].reshape(n, fen)
        rms = np.sqrt((tronque ** 2).mean(axis=1))
        seuil = 10 ** (seuil_db / 20)
        silencieux = rms < seuil
        # Regrouper les fenêtres silencieuses contiguës
        silences = []
        debut = None
        for i, s in enumerate(silencieux):
            if s and debut is None:
                debut = i
            elif not s and debut is not None:
                duree = (i - debut) * 0.1
                if duree >= duree_min:
                    silences.append({'debut': round(debut * 0.1, 1),
                                     'fin': round(i * 0.1, 1),
                                     'duree': round(duree, 1)})
                debut = None
        if debut is not None:
            duree = (len(silencieux) - debut) * 0.1
            if duree >= duree_min:
                silences.append({'debut': round(debut * 0.1, 1),
                                 'fin': round(len(silencieux) * 0.1, 1),
                                 'duree': round(duree, 1)})
        return silences
    except Exception:
        return []


def analyser_niveaux(path):
    """Ancien nom conservé pour compatibilité (lent, via ffmpeg)."""
    p = subprocess.run(
        ['ffmpeg', '-v', 'info', '-i', str(path),
         '-af', 'volumedetect', '-f', 'null', '/dev/null'],
        capture_output=True, text=True, timeout=600)
    out = p.stderr
    max_vol = re.search(r'max_volume:\s*(-?[\d.]+)\s*dB', out)
    mean_vol = re.search(r'mean_volume:\s*(-?[\d.]+)\s*dB', out)
    return {
        'max_db': float(max_vol.group(1)) if max_vol else None,
        'mean_db': float(mean_vol.group(1)) if mean_vol else None,
    }


def detecter_silences(path, seuil_db=-40, duree_min=3.0):
    """Ancien nom conservé pour compatibilité (lent, via ffmpeg)."""
    p = subprocess.run(
        ['ffmpeg', '-v', 'info', '-i', str(path),
         '-af', f'silencedetect=noise={seuil_db}dB:d={duree_min}',
         '-f', 'null', '/dev/null'],
        capture_output=True, text=True, timeout=600)
    silences = []
    for m in re.finditer(
            r'silence_start:\s*([\d.]+).*?silence_end:\s*([\d.]+)',
            p.stderr, re.DOTALL):
        debut, fin = float(m.group(1)), float(m.group(2))
        if fin - debut >= duree_min:
            silences.append({'debut': debut, 'fin': fin,
                             'duree': round(fin - debut, 1)})
    return silences


def verifier_technique(path, wav_path=None):
    """Vérification technique complète. Retourne dict structuré.

    wav_path : chemin du WAV déjà extrait (pour analyse audio rapide via numpy).
    Si None, utilise les filtres ffmpeg (plus lent).
    """
    fiches = []
    commentaires = []  # (secondes, texte)
    alertes = []

    info = ffprobe_info(path)
    streams = info.get('streams', [])
    fmt = info.get('format', {})

    video = next((s for s in streams if s.get('codec_type') == 'video'), {})
    audio = next((s for s in streams if s.get('codec_type') == 'audio'), {})

    # --- VIDÉO ---
    codec_v = video.get('codec_name', '?').upper()
    larg = video.get('width', '?')
    haut = video.get('height', '?')
    fps_raw = video.get('r_frame_rate', '0/1')
    try:
        n, d = map(int, fps_raw.split('/'))
        fps = round(n / d, 2) if d else 0
    except Exception:
        fps = 0
    duree = float(fmt.get('duration', 0) or 0)
    debit_v = int(video.get('bit_rate', 0) or 0) // 1000

    fiches.append(f"Vidéo : {codec_v} {larg}x{haut} {fps} im/s, "
                  f"{debit_v} kb/s, durée {duree:.0f}s")

    # Règles vidéo
    if codec_v not in ('H264', 'AVC', 'HEVC', 'H265'):
        alertes.append(f"Codec vidéo inhabituel : {codec_v} (attendu H.264)")
    if isinstance(larg, int) and larg < 1280:
        alertes.append(f"Résolution faible : {larg}x{haut} (< 720p)")
    if fps and fps not in (23.98, 24, 25, 29.97, 30, 50, 59.94, 60):
        alertes.append(f"Cadence inhabituelle : {fps} im/s")

    # --- AUDIO ---
    codec_a = audio.get('codec_name', '?').upper()
    canaux = audio.get('channels', 0)
    layout = audio.get('channel_layout', '')
    freq = audio.get('sample_rate', '?')
    debit_a = int(audio.get('bit_rate', 0) or 0) // 1000

    label_canaux = 'stéréo' if canaux == 2 else ('mono' if canaux == 1 else f'{canaux} canaux')
    fiches.append(f"Audio : {codec_a} {label_canaux} ({layout}), "
                  f"{freq} Hz, {debit_a} kb/s")

    # Règles audio
    if codec_a not in ('AAC', 'MP3', 'PCM_S16LE', 'AC3'):
        alertes.append(f"Codec audio inhabituel : {codec_a}")
    if canaux == 1:
        alertes.append("Audio MONO détecté — vérifier si stéréo attendue")
        commentaires.append((1, "⚠️ Audio en mono — confirmer que c'est voulu "
                                "(stéréo attendue par défaut)."))
    elif canaux > 2:
        alertes.append(f"Audio {canaux} canaux — vérifier la compatibilité diffusion")
    if str(freq) not in ('44100', '48000'):
        alertes.append(f"Fréquence inhabituelle : {freq} Hz (attendu 44,1 ou 48 kHz)")

    # --- NIVEAUX ---
    if audio:
        # Méthode rapide via WAV si disponible, sinon ffmpeg
        if wav_path and Path(wav_path).exists():
            niveaux = analyser_niveaux_wav(wav_path)
        else:
            niveaux = analyser_niveaux(path)
        max_db = niveaux['max_db'] if niveaux else None
        mean_db = niveaux['mean_db'] if niveaux else None
        if max_db is not None:
            fiches.append(f"Niveaux : crête {max_db:.1f} dB, moyen {mean_db:.1f} dB")
            if max_db > -1:
                alertes.append(f"ÉCRÊTAGE : crête à {max_db:.1f} dB (risque de saturation)")
                commentaires.append((1, f"🔴 Écrêtage audio détecté (crête {max_db:.1f} dB) — "
                                        "risque de saturation, à corriger."))
            elif max_db < -30:
                alertes.append(f"Niveau très faible : crête à {max_db:.1f} dB")
                commentaires.append((1, f"⚠️ Niveau audio très faible (crête {max_db:.1f} dB) — "
                                        "envisager une normalisation."))
            elif -20 <= max_db <= -12:
                fiches.append("Niveaux sains (crêtes -12 à -20 dB)")
        else:
            fiches.append("Niveaux : piste muette ou illisible")

        # --- SILENCES ---
        if wav_path and Path(wav_path).exists():
            silences = detecter_silences_wav(wav_path)
        else:
            silences = detecter_silences(path)
        if silences:
            for s in silences[:5]:  # max 5 commentaires
                alertes.append(f"Silence mort de {s['duree']}s à "
                               f"{s['debut']:.0f}s")
                commentaires.append((s['debut'], f"🔇 Silence mort de {s['duree']}s "
                                                 "détecté — vérifier si voulu."))
            if len(silences) > 5:
                fiches.append(f"+ {len(silences) - 5} autres silences détectés")
        else:
            fiches.append("Aucun silence mort détecté (> 3s)")

    # --- SYNTHÈSE ---
    sain = not any('ÉCRÊTAGE' in a or 'MONO' in a for a in alertes)
    if not alertes:
        fiches.insert(0, "✅ Technique saine : aucun problème détecté.")
    else:
        fiches.insert(0, f"⚠️ {len(alertes)} point(s) technique(s) à vérifier.")

    return {
        'fiches': fiches,
        'commentaires': commentaires,
        'alertes': alertes,
        'sain': sain,
        'specs': {
            'codec_video': codec_v, 'resolution': f"{larg}x{haut}",
            'fps': fps, 'duree_sec': round(duree),
            'codec_audio': codec_a, 'canaux': canaux,
            'frequence': str(freq),
        },
    }


if __name__ == '__main__':
    import sys
    r = verifier_technique(sys.argv[1])
    print(json.dumps(r, ensure_ascii=False, indent=2))
