#!/usr/bin/env python3
"""Sauvegarde des rapports QC dans Google Drive (dossier « Factory QC — Rapports »).

Deux modes d'authentification, essayés dans l'ordre :
1. Compte de service Google (Render/prod) via la variable d'environnement
   GOOGLE_SERVICE_ACCOUNT_JSON (contenu JSON de la clé).
2. Repli local : `hatch_gws_cli` (compte Google connecté de l'utilisateur).

Le dossier cible se configure via DRIVE_RAPPORTS_FOLDER_ID (défaut : dossier
« Factory QC — Rapports » créé le 2026-10-07).

Toutes les fonctions sont « best-effort » : en cas d'échec elles loggent
et rendent (None, None) / [] sans jamais lever d'exception.
"""
import json
import os
import shutil
import subprocess

DOSSIER_RAPPORTS_DEFAUT = "1eLTzHaDWsAsjz772vE3AQGk3Hn0wUWJ8"


def dossier_rapports():
    return os.environ.get("DRIVE_RAPPORTS_FOLDER_ID", DOSSIER_RAPPORTS_DEFAUT)


def _client_service_account():
    """Client Drive via compte de service (Render). None si indisponible."""
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        return None
    try:
        info = json.loads(raw)
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/drive"])
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"[drive] compte de service indisponible : {e}", flush=True)
        return None


def _cli_disponible():
    return shutil.which("hatch_gws_cli") is not None


def _sauvegarder_sa(chemin_rapport, nom_cible):
    svc = _client_service_account()
    if svc is None:
        return (None, None)
    from googleapiclient.http import MediaFileUpload
    meta = {"name": nom_cible,
            "parents": [dossier_rapports()],
            "mimeType": "text/markdown"}
    media = MediaFileUpload(str(chemin_rapport), mimetype="text/markdown",
                            resumable=False)
    f = svc.files().create(body=meta, media_body=media,
                           fields="id,webViewLink").execute()
    print(f"[drive] rapport sauvegardé : {f.get('webViewLink')}", flush=True)
    return (f.get("id"), f.get("webViewLink"))


def _sauvegarder_cli(chemin_rapport, nom_cible):
    if not _cli_disponible():
        return (None, None)
    p = subprocess.run(
        ["hatch_gws_cli", "drive", "+upload", str(chemin_rapport),
         "--parent", dossier_rapports(), "--name", nom_cible,
         "--format", "json"],
        capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        print(f"[drive] upload CLI échec : {p.stderr[:200]}", flush=True)
        return (None, None)
    try:
        fid = json.loads(p.stdout).get("id")
    except Exception:
        return (None, None)
    if not fid:
        return (None, None)
    # Récupérer le lien de partage
    p2 = subprocess.run(
        ["hatch_gws_cli", "drive", "files", "get", "--params",
         json.dumps({"fileId": fid, "fields": "id,webViewLink"})],
        capture_output=True, text=True, timeout=60)
    try:
        lien = json.loads(p2.stdout).get("webViewLink") if p2.returncode == 0 else None
    except Exception:
        lien = None
    print(f"[drive] rapport sauvegardé (id {fid})", flush=True)
    return (fid, lien)


def sauvegarder_rapport(chemin_rapport, nom_cible):
    """Upload le rapport dans le dossier Drive.

    Retourne (file_id, webViewLink) ou (None, None) en cas d'échec.
    Ne lève jamais.
    """
    for fn in (_sauvegarder_sa, _sauvegarder_cli):
        try:
            res = fn(chemin_rapport, nom_cible)
            if res and res[0]:
                return res
        except Exception as e:
            print(f"[drive] {fn.__name__} : {e}", flush=True)
    return (None, None)


def lister_rapports(limite=50):
    """Liste les rapports du dossier Drive : [{id, name, webViewLink, modifiedTime}]."""
    svc = _client_service_account()
    if svc is not None:
        try:
            r = svc.files().list(
                q=f"'{dossier_rapports()}' in parents and trashed=false",
                pageSize=limite, orderBy="modifiedTime desc",
                fields="files(id,name,webViewLink,modifiedTime)").execute()
            return r.get("files", [])
        except Exception as e:
            print(f"[drive] liste SA : {e}", flush=True)
    if _cli_disponible():
        try:
            p = subprocess.run(
                ["hatch_gws_cli", "drive", "files", "list", "--params",
                 json.dumps({
                     "q": f"'{dossier_rapports()}' in parents and trashed=false",
                     "pageSize": limite, "orderBy": "modifiedTime desc",
                     "fields": "files(id,name,webViewLink,modifiedTime)"})],
                capture_output=True, text=True, timeout=60)
            if p.returncode == 0:
                return json.loads(p.stdout).get("files", [])
        except Exception as e:
            print(f"[drive] liste CLI : {e}", flush=True)
    return []
