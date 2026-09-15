#!/usr/bin/env bash
# One-shot: create/verify oss.wesleymatos.dev CNAME using the Cloudflare token
# from 1Password (Hermes vault, "CloudFlare API Token").
# The token streams op -> python stdin; never written to disk, never echoed.
set -euo pipefail
op read 'op://Hermes/CloudFlare API Token/credential' | python3 -c "
import sys, json, urllib.request
tok = sys.stdin.read().strip()
print('token received, length:', len(tok))
req = urllib.request.Request('https://api.cloudflare.com/client/v4/zones?name=wesleymatos.dev', headers={'Authorization': 'Bearer ' + tok})
z = json.load(urllib.request.urlopen(req))
if not z.get('success') or not z.get('result'):
    print('zone lookup failed:', z.get('errors')); sys.exit(1)
zid = z['result'][0]['id']
print('zone found')
body = json.dumps({'type':'CNAME','name':'oss','content':'wesleymatosdev.github.io','proxied':False}).encode()
q = urllib.request.Request(f'https://api.cloudflare.com/client/v4/zones/{zid}/dns_records?name=oss.wesleymatos.dev&type=CNAME', headers={'Authorization': 'Bearer ' + tok})
existing = json.load(urllib.request.urlopen(q)).get('result') or []
if existing:
    req = urllib.request.Request(f'https://api.cloudflare.com/client/v4/zones/{zid}/dns_records/' + existing[0]['id'], data=body, headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method='PUT')
    print('updating existing record')
else:
    req = urllib.request.Request(f'https://api.cloudflare.com/client/v4/zones/{zid}/dns_records', data=body, headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'})
    print('creating record')
r = json.load(urllib.request.urlopen(req))
print('success:', r.get('success'), '| errors:', r.get('errors'))
"
