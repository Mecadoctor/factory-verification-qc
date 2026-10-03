#!/usr/bin/env python3
"""Authentification Adobe OAuth2 pour l'API Frame.io v4.

La v4 exige OAuth2 (authorization_code). Ce module :
- échange un refresh_token contre un access_token frais (mis en cache en mémoire),
- est utilisé par worker.py pour chaque appel API.

Variables d'environnement :
  ADOBE_CLIENT_ID      (défaut: projet « Muse QC workflow »)
  ADOBE_CLIENT_SECRET  (obligatoire)
  ADOBE_REFRESH_TOKEN  (obtenu via /oauth/login -> /oauth/callback, à copier dans Render)
"""
import json, os, time, urllib.parse, urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
CLIENT_ID = os.environ.get('ADOBE_CLIENT_ID', '0eeaa9bf24224fefa381ce97784f7fb3')
CLIENT_SECRET = os.environ.get('ADOBE_CLIENT_SECRET', '')
TOKEN_URL = 'https://ims-na1.adobelogin.com/ims/token/v3'

_cache = {'token': None, 'expire_a': 0}

def _refresh_token_value():
    tok = os.environ.get('ADOBE_REFRESH_TOKEN', '').strip()
    if tok:
        return tok
    p = os.path.join(BASE, 'adobe_refresh_token.txt')
    try:
        if os.path.exists(p):
            return open(p).read().strip()
    except Exception:
        pass
    return ''

def get_access_token():
    """Retourne un access_token Adobe IMS valide (rafraîchi si besoin)."""
    now = time.time()
    if _cache['token'] and now < _cache['expire_a'] - 60:
        return _cache['token']
    rt = _refresh_token_value()
    if not rt:
        raise RuntimeError("ADOBE_REFRESH_TOKEN manquant : autoriser via /oauth/login puis copier le refresh token dans Render.")
    if not CLIENT_SECRET:
        raise RuntimeError("ADOBE_CLIENT_SECRET manquant.")
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': rt,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method='POST',
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Refresh OAuth échoué (HTTP {e.code}) : re-autoriser via /oauth/login.")
    token = resp.get('access_token')
    if not token:
        raise RuntimeError(f"Pas d'access_token dans la réponse IMS : {str(resp)[:150]}")
    _cache['token'] = token
    _cache['expire_a'] = now + int(resp.get('expires_in', 3600))
    # Un nouveau refresh_token peut être retourné (rotation)
    if resp.get('refresh_token') and resp['refresh_token'] != rt:
        try:
            open(os.path.join(BASE, 'adobe_refresh_token.txt'), 'w').write(resp['refresh_token'])
        except Exception:
            pass
    return token
