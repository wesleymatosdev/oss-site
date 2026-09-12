# Verification evidence — sections-and-nav (Phases 0–4)

Executor: oss-site-exec · Branch `sections-and-nav` · 2026-09-11
Plan: `~/projects/personal/swarm/plans/oss-site-nav-sections-plan.md`

## Commits (in order)

| commit | phase | content |
|---|---|---|
| `48c351e` | 0 | baseline regeneration diff (generated 2026-09-10, stars null→0) |
| `37e7e64` | 1 | collect.py schema + data corrections; regenerated outputs |
| `865d7a7` | 2 | §3.3 honesty rewords (xcap-recorder, skills, unfit-rs, colibri, gnhf) |
| `28117ef` | 3 | renderer: full sections + compact rows coexist; visibility link gating |
| `5f86269` | 4 | shared nav partial + CSS; `.back-link` deleted; sync-nav.py |

## Per-phase results

- **Phase 0** — `git status` clean after baseline commit (only the three
  deliberately-untracked files remain: `.hermes.md`, `scripts/cf_dns_oss.py`,
  `scripts/oss-dns-once.sh` — never touched, never run).
- **Phase 1** — `python3 scripts/collect.py` → `OK: 77 projects across 8 groups`,
  **zero WARNING lines**. 25/25 JSON assertions pass
  (`phase1-assertions.txt`): totals, per-group 8/11/4/1/8/40/2/3, exactly 21
  `full=true`, backfilled urls, absences (tmux-axi / unfit-madeline /
  hermes-ops), zcode-cli → `kingsword09/zcode-cli`, private four
  `public=false`, site urls. Idempotence: same-day rerun byte-identical
  (md5-verified twice).
- **Phase 2** — retired-claims grep clean on all three generated files
  (`battle-tested` / `cross-platform` / `kept alive with real work`). All 21
  full sections' `purpose`/`state`/`state_note` mechanically diffed against
  the plan's §3.2 block: verbatim (`phase2-copy-check.txt`).
- **Phase 3** — headless Chrome over `file://`, 15/15 pass
  (`phase3-results.txt`, harness `phase3-assertions.mjs`): 21 `.card-full`,
  77 `.card`, per-group counts match DOM, filter "rust"→23/77 consistent,
  "zzzz"→all hidden + "0 of 77", clear→77, console-art no repo anchor +
  never-published note, website → wesleymatos.dev site anchor only,
  fleet-bus/auto-permissions `soon` badges + no anchors, single stars chip
  (spinning-cube ★ 3), session-rc "v0 — working", unfit-rs "PoC —
  unmaintained" + Lavish. llms.txt manual reads recorded. Screenshot:
  `phase3-fullpage.png`.
- **Phase 4** — headless Chrome over `file://`, 9/9 pass
  (`phase4-results.txt`, harness `phase4-assertions.mjs`): exactly one
  `nav.site-nav`, direct `<body>` child, outside `#catalog`/`.site-header`,
  above it in DOM order; 5 links; single `aria-current` → oss.wesleymatos.dev;
  `.back-link` absent from DOM and CSS; nav fixed top 22px / right 26px,
  z 3 over `.page` z 1; no-JS run still renders the 5-link nav.
  `sync-nav.py` round-trip on the installed block is byte-identical and it
  refuses sentinel-less files. Screenshot: `phase4-viewport.png`.

## Plan deviations (both minimal, forced by facts on the ground)

1. **IGNORE_LOCAL gained `tmux-axi` and `orca-fork`.** The plan's zero-warning
   gate failed on first regen: `tmux-axi` has a local dir (API_EXCLUDE only
   silences the API side, not the walk) and `orca-fork` is an upstream clone
   of stablyai/orca the planner didn't know about. IGNORE_LOCAL is the plan's
   own mechanism for "local dirs deliberately absent"; catalog content is
   unchanged either way.
2. **FULL_SECTIONS copy landed with the Phase 1 schema**, not Phase 2 — plan
   §6 requires "exactly 21 `full=true`" at Phase 1, which is impossible with
   an empty table. Phase 2 then landed the §3.3 description rewords and ran
   the copy verification, matching the brief's phase semantics.

## Notes

- Plan §2.4 says "ten entries gain real urls via backfill" but enumerates
  nine names; exactly those nine gain urls against the live API (fleet-bus /
  auto-permissions correctly stay local-only). Assertions used the
  enumerated list.
- Plan §6 Phase 2's grep names `data/projects.js`; the generated JS lives at
  `www/projects.js` — grep run against the real generated files.
- GitHub API state verified 2026-09-11: 103 public repos for wesleymatosdev
  (page 2 = 3 forks, so the per_page=100 fetch misses nothing non-fork),
  2 for wesleymatos-bot (colibri, gnhf).
