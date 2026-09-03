# oss-site

Source for **[oss.wesleymatos.dev](https://oss.wesleymatos.dev)** — the public catalog of
Wesley's open-source work. Sits next to the main site at
[wesleymatos.dev](https://wesleymatos.dev) and shares its dark nebula/starfield look.

## What's here

```
data/projects.json   source of truth — every project, grouped and described
scripts/collect.py   regenerates the data files (see below)
www/                 the static site — no build step, no npm, no CDNs
CNAME                custom domain: oss.wesleymatos.dev
.github/workflows/deploy.yml   deploys www/ to GitHub Pages on push to main
```

## data/projects.json is the source of truth

The site renders whatever is in `data/projects.json` (copied verbatim into
`www/projects.js` at generation time so the page needs no `fetch()` and previews
over `file://`). Each project entry carries: `name`, `description`, `language`,
`url` (GitHub remote, or `null` for local-only work), `stars`, `local`, and
`category` — which is one of the display groups:

- `agent-infra` — tools around Hermes, local models, and the agent loop
- `cli-tool` — the axi family and other CLIs
- `library`, `benchmark`, `website`, `experiment`
- `maintained-forks` — forks kept alive with real work (colibri, gnhf)
- `contributions` — work toward upstreams (memory-os, deskflow)

Local-only repos (no GitHub remote yet) render as dashed cards marked **soon**
instead of a dead link.

## Regenerating the data

`scripts/collect.py` merges the public GitHub API (`wesleymatosdev` +
`wesleymatos-bot`, non-fork repos) with a curated table for local/private repos
and rewrites `data/projects.json`, `www/projects.js`, and `www/llms.txt`:

```sh
python3 scripts/collect.py
```

Needs network for the API. New local repos show up as a warning until they're
added to `CURATED` or `API_CATEGORY` inside the script; forks are only listed
when curated. Descriptions come from each repo's README or GitHub description —
never invented.

## Previewing locally

```sh
python3 -m http.server 8000 --directory www
# open http://localhost:8000
```

No build step, no dependencies.

## Deploying

Push to `main` — the GitHub Actions workflow uploads `www/` and deploys it to
GitHub Pages. The `CNAME` files (repo root and `www/`) pin the custom domain
`oss.wesleymatos.dev`; point the DNS `CNAME` at the Pages endpoints once in
repo settings.
