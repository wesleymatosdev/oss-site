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
over `file://`). Each project entry carries, in this key order:

| field | meaning |
|---|---|
| `name` | catalog name (repo name, or the curated alias) |
| `description` | one-line summary — factual, third-person, true of the repo today |
| `language` | primary language, or `null` |
| `url` | GitHub remote (`.git` stripped), or `null` for local-only work |
| `stars` | build-time star count from the API; `null` when the repo is not on the API |
| `local` | true = no public repo to link (renders as a dashed **soon** card) |
| `public` | false = the repo is private or absent — renderers never link the url |
| `site` | live URL to link instead of the repo (website, blog, demo, skills) |
| `full` | true = render as a full brief section rather than a compact row |
| `purpose` | goals/what-it-does paragraph (full sections only, else `null`) |
| `state` | short honest status label, e.g. `working`, `PoC — unmaintained` |
| `state_note` | optional caveat/evidence line shown next to the state badge |
| `category` | one of the display groups |

Curated rows whose repo went public after being added are healed at generation
time: the API match backfills `url`, `stars`, `local=false`, `public=true`.
Private repos stay unlinked — `www/llms.txt` shows `source not public` for
them, and entries with a `site` show the live URL instead.

`category` is one of:

- `agent-infra` — tools around Hermes, local models, and the agent loop
- `cli-tool` — the axi family and other CLIs
- `library`, `benchmark`, `website`, `experiment`
- `maintained-forks` — forks of upstream projects, published as-is
- `contributions` — work toward upstreams (memory-os, zcode-cli, deskflow)

Projects marked `full` render as stacked full-width sections with their
`purpose`/`state`/`state_note` copy; the rest stay compact grid rows. Both
shapes share the `card` class, so the live filter covers both.

## Shared site nav

`www/index.html` carries the wesleymatos.dev nav inside `wm-nav:begin/end`
sentinels (CSS likewise in `www/css/style.css`, plus oss-specific `:root`
token mapping outside the sentinels). Regenerate the HTML block across all
four hand-written sites by hand with:

```sh
python3 scripts/sync-nav.py           # with the Open Source link
python3 scripts/sync-nav.py --no-oss  # pre-DNS: omit the oss.wesleymatos.dev link
```

The script only maintains existing sentinel blocks; first installation per
site is a manual edit. The blog is configured via `menu:` in its
`marmite.yaml` instead — the script prints the equivalent YAML as a reminder.

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
