#!/usr/bin/env python3
"""Read the Cloudflare DNS token from 1Password and create/verify the
oss.wesleymatos.dev CNAME. The token never reaches stdout/stderr or any file.

Expected 1Password item (override with OP_ITEM_REF env var, e.g. 'Cloudflare'):
  op://<vault>/<item>/credential  (or a field named token/api key)

Falls back to CLOUDFLARE_API_KEY from ~/.hermes/.env if 1Password has no match.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ENV_PATH = os.path.expanduser("~/.hermes/.env")
ZONE_NAME = "wesleymatos.dev"
RECORD_NAME = "oss.wesleymatos.dev"
TARGET = "wesleymatosdev.github.io"
OP = "/opt/homebrew/bin/op"


def load_env(path):
    env = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env[key] = val.strip().strip('"').strip("'")
    return env


def token_from_1password():
    """Return (token, mode) or (None, None). Token never printed."""
    sa = load_env(ENV_PATH).get("OP_SERVICE_ACCOUNT_TOKEN")
    if not sa:
        return None, None
    env = {**os.environ, "OP_SERVICE_ACCOUNT_TOKEN": sa}
    item = os.environ.get("OP_ITEM_REF", "Hermes/CloudFlare API Token")
    for field in ("credential", "token", "api key", "password"):
        ref = f"op://{item}/{field}" if "/" not in item else f"{item}/{field}"
        r = subprocess.run([OP, "read", ref], capture_output=True, text=True,
                           env=env, timeout=45)
        tok = (r.stdout or "").strip()
        if r.returncode == 0 and tok and not tok.startswith("ERROR"):
            return tok, f"1Password {item}/{field}"
    return None, None


def cf(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4" + path,
        data=data, method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        print(f"  CF API error HTTP {e.code}: {detail}")
        raise


def main():
    token, source = token_from_1password()
    if not token:
        token = load_env(ENV_PATH).get("CLOUDFLARE_API_KEY")
        source = "~/.hermes/.env CLOUDFLARE_API_KEY" if token else None
    if not token:
        print("no Cloudflare token available (1Password miss + no .env fallback)")
        sys.exit(1)
    print(f"token sourced from: {source} (value hidden)")

    acct = load_env(ENV_PATH).get("CLOUDFLARE_ACCOUNT_ID")
    q = f"/zones?name={ZONE_NAME}" + (f"&account.id={acct}" if acct else "")
    zones = cf("GET", q, token).get("result") or []
    if not zones:
        print("zone wesleymatos.dev not visible to this token")
        sys.exit(1)
    zone_id = zones[0]["id"]
    print("zone found")

    existing = cf("GET", f"/zones/{zone_id}/dns_records?name={RECORD_NAME}&type=CNAME", token).get("result") or []
    body = {"type": "CNAME", "name": "oss", "content": TARGET, "proxied": False, "ttl": 1}
    if existing:
        out = cf("PUT", f"/zones/{zone_id}/dns_records/{existing[0]['id']}", token, body)
        print("updated:", out.get("success"), out.get("errors"))
    else:
        out = cf("POST", f"/zones/{zone_id}/dns_records", token, body)
        print("created:", out.get("success"), out.get("errors"))


if __name__ == "__main__":
    main()
