# SWARM REPORT — oss-site

**Worker:** zcode (GLM) · **Date:** 2026-09-03 · **Repo:** `/Users/wesleymatos/projects/personal/oss-site`

## What was built

A static catalog site of Wesley's open-source work for **oss.wesleymatos.dev**:

- **72 projects across 8 groups** (agent-infra 6, cli-tool 10, library 4, benchmark 1,
  website 7, experiment 40, maintained-forks 2, contributions 2), merged from the
  public GitHub API (`wesleymatosdev`: 87 repos, `wesleymatos-bot`: 2 repos; the org
  `wesleymatosdev` does not exist — API 404) and a walk of `~/projects/personal`
  (31 git repos + `gnhf-lab`).
- **Dark nebula theme matched to wesleymatos.dev**: `#030209` background, canvas
  starfield (copied from `website/www/starfield.js`, warp intro enabled), purple/blue/cyan
  gradient title, soft-glow rounded cards, system font stack, live search filter.
  Mobile-responsive: single column under 430px, no fixed widths.
- **No build step, no npm, no CDNs** — plain HTML/CSS/JS; data is baked into
  `www/projects.js` (generated from `data/projects.json`) so the page renders without
  `fetch()` and previews over `file://` or any static server.
- Local-only repos (no GitHub remote: 15 of 72) render as dashed cards marked **soon**
  instead of dead links. Cards: name, description, language badge, stars when > 0
  (only `spinning-cube` has stars: 3), external link `target="_blank" rel="noopener"`.

All 24 known repos from the brief are included. Two mappings worth noting: the local
`hermes-sdk` dir publishes as `hermes-agent-rs` (its actual remote), and `demo-worker`
publishes as `pages-proxy`. `gnhf-lab` has content (lane objectives, launch scripts) and
is included as a local-only experiment.

## Files created

```
data/projects.json          source of truth (72 projects, 8 groups)
scripts/collect.py          regenerates data/projects.json, www/projects.js, www/llms.txt
www/index.html              page shell (header, filter, catalog mount, footer)
www/css/style.css           nebula theme
www/js/app.js               renders groups/cards + live filter
www/starfield.js            adapted from wesleymatos.dev (Wesley's own file)
www/projects.js             generated data as a JS global
www/llms.txt                plain-text index (one line per project)
www/favicon.svg             star favicon (avoids missing-icon console noise)
www/CNAME                   oss.wesleymatos.dev (copy for the Pages artifact)
CNAME                       oss.wesleymatos.dev (repo root, per brief)
.github/workflows/deploy.yml  deploy www/ to GitHub Pages on push to main
README.md                   what/why, data model, regenerate + preview instructions
```

## Gate results

| # | Gate | Result |
|---|------|--------|
| 1 | `python3 -m json.tool data/projects.json` parses | **PASS** |
| 2 | Every asset path referenced by index.html exists on disk | **PASS** (6/6 relative refs; also verified HTTP 200 for all 8 served paths) |
| 3 | No absolute filesystem paths leaked into the HTML | **PASS** (no `/Users/` in any www/ file) |
| 4 | Zero external CDN/script references in www/ | **PASS** (no external `<script src>`/`<link href>`/`@import`; only `<a href>` links to wesleymatos.dev and github.com) |
| 5 | Headless render: zero console errors, no horizontal overflow at 390px | **PASS (static check)** — see note |

**Gate 5 note:** browser tooling was attempted twice in this session and the runtime
reported "Browser control is unavailable for this node_repl session", so the brief's
fallback applied — static checks instead:

- `node --check` passes on all three JS files (no syntax errors).
- Every referenced asset serves HTTP 200 (no 404-driven console errors; favicon included).
- DOM contract verified: all ids `app.js` requires (`#catalog`, `#filter`, `#count`,
  `#generated`) exist in the HTML; `projects.js` defines `window.OSS_PROJECTS` with 8 groups.
- The actual render path of `app.js` was executed in Node against a minimal DOM shim:
  renders 72 cards (15 soon + 57 linked) and the correct count text without throwing.
- 390px overflow audit: viewport meta present; content column = 390 − 32 padding = 358px
  ≥ the 280px `minmax()` floor (single column); `overflow-wrap: anywhere` on names and
  descriptions; CSS contains no fixed pixel widths (only `max-width`s); `overflow-x:
  hidden` on body as a backstop; the title uses `clamp(2rem, 6vw, 3.1rem)`.

## Commits

```
461c336 docs: README with data model, regeneration, and preview steps
79815b0 ci(deploy): GitHub Pages workflow + oss.wesleymatos.dev CNAME
cf55632 feat(site): nebula-themed static catalog in www/
f9fd22f feat(data): project catalog from GitHub API + curated local repos
```

(plus the commit adding this report). Working tree clean; `main` branch; no remote
operations were performed — no push, no `gh`.

## Data decisions & caveats

- **Descriptions** come from each repo's README, Cargo.toml/brief, or GitHub
  description — nothing invented. A handful of old public repos with neither
  (e.g. `boilerplate`, `kafka-with-java`, `web-rtc-video-call`) are listed with a
  muted "—" description rather than a guessed one.
- **Forks excluded by design:** of the ~35 forks on `wesleymatosdev`, only curated
  ones are listed — `colibri` and `gnhf` (maintained-forks, both on the bot account).
  The rest (prisma, qdrant, drizzle-orm, hermes-agent, firstmate, xcap, …) show no
  public evidence of divergent work; adding one is a two-line change in
  `scripts/collect.py` (`CURATED`).
- **deskflow-pentesting** is grouped under contributions (its description says it
  implements deskflow/deskflow#8010).
- **Linked but currently private:** six cards point at exact existing remotes that are
  not in the public API, i.e. private repos — `unfit`, `unfit-madeline`, `console-art`,
  `demo`, `skills`, `website` (and `blog` has no remote at all, so it's a "soon" card).
  Visitors will see GitHub 404s until those are made public. The brief said to use the
  existing remote URL exactly, which is what was done.
- **`usage-dash`** has 0 commits but real source (axum server over the Hermes state DB),
  so it's included as a "soon" card.

## Left unfinished / manual steps

- **Publishing**: repo has no remote; pushing to GitHub and enabling Pages (Source:
  GitHub Actions) + adding the `oss.wesleymatos.dev` custom domain in repo settings are
  manual steps — out of scope per the hard rules.
- **DNS**: `oss.wesleymatos.dev` CNAME to the Pages endpoints must be added wherever
  wesleymatos.dev DNS lives.
- Live-browser pass (console/overflow) can be re-run manually: `python3 -m http.server
  8000 --directory www` and open the page.
