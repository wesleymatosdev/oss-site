#!/usr/bin/env python3
"""Collect project data for oss.wesleymatos.dev.

Merges two sources into data/projects.json:

  1. The public GitHub API (wesleymatosdev + wesleymatos-bot).
     Only non-fork repos are taken from the API, except the two maintained
     forks listed in CURATED below (colibri, gnhf).
  2. A curated table for local/private repos under ~/projects/personal —
     descriptions are derived from each repo's README / Cargo.toml / brief.

Outputs:
  data/projects.json   — source of truth for the site
  www/projects.js      — same data as a JS global (lets index.html render
                         without fetch(), so file:// preview works)
  www/llms.txt         — plain-text index, one line per project

Regenerate with:  python3 scripts/collect.py   (needs network for the API)
"""

import json
import subprocess
import urllib.request
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAL_DIR = Path.home() / "projects" / "personal"
GENERATED = date.today().isoformat()

GITHUB_USERS = ["wesleymatosdev", "wesleymatos-bot"]

# Display groups, in site order.
GROUPS = [
    ("agent-infra", "Agent infrastructure",
     "Tools around Hermes, local models, and the agent loop."),
    ("cli-tool", "CLI tools",
     "Small, sharp command-line utilities — the axi family and friends."),
    ("library", "Libraries",
     "Reusable libraries and SDKs."),
    ("benchmark", "Benchmarks",
     "Harnesses that measure instead of guess."),
    ("website", "Websites & apps",
     "Sites, apps, and web experiments."),
    ("experiment", "Experiments & learning",
     "Spikes, challenges, and learning repos."),
    ("maintained-forks", "Forks",
     "Forks of upstream projects, published as-is — no local changes yet."),
    ("contributions", "Contributions",
     "Work done toward upstream projects."),
]

# Curated entries: local and/or private repos the public API can't describe.
# url is the repo's existing remote, exactly as configured; null = local only.
# local dirs that publish under a different GitHub name map via LOCAL_ALIAS.
CURATED = {
    "unfit": {
        "category": "website", "language": "HTML",
        "url": "https://github.com/wesleymatosdev/unfit.git", "public": False,
        "description": "LAN-only review hub for visual artifacts — click-to-annotate DOM elements, queue comments, durable local SQLite storage",
    },
    "unfit-rs": {
        "category": "cli-tool", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/unfit-rs.git", "public": True,
        "description": "unf.it review tool — Rust rewrite: local-first visual review hub for iterating on websites with element-scoped feedback",
    },
    "ollama-axi": {
        "category": "cli-tool", "language": "Rust", "url": None, "public": True,
        "description": "Agent-grade model management for Ollama — gc orphaned blobs and aborted pulls, inspect the real store, reclaim dead weight",
    },
    "herdr-axi": {
        "category": "cli-tool", "language": "Rust", "url": None, "public": True,
        "description": "AXI-discipline wrapper around the herdr multiplexer CLI",
    },
    "scp-axi": {
        "category": "cli-tool", "language": "Rust", "url": None, "public": True,
        "description": "Unattended file transfer to SSH-key-authenticated hosts — no interactive prompts, dry-run default, human + --json output",
    },
    "session-rc": {
        "category": "cli-tool", "language": "Rust", "url": None, "public": True,
        "description": "Thin CLI to remote-control one exact live Hermes gateway session from a phone",
    },
    "session-categorizer": {
        "category": "agent-infra", "language": "Python", "url": None, "public": True,
        "description": "Deterministic, no-LLM categorizer for Hermes session databases — extracts decisions, constraints and blockers with citations",
    },
    "anti-babysitting-pipeline": {
        "category": "agent-infra", "language": "Shell", "url": None, "public": True,
        "description": "Deterministic support code for Hermes's autonomous Kanban supervisor — wakes the supervisor only when the board changes",
    },
    "auto-permissions": {
        "category": "agent-infra", "language": "TypeScript", "url": None, "public": False,
        "description": "ZCode plugin adding a Claude-Code-style auto permission classifier — safe actions auto-approved, dangerous ones denied with a reason",
    },
    "usage-dash": {
        "category": "agent-infra", "language": "Rust", "url": None, "public": True,
        "description": "Read-only web dashboard over the local Hermes state DB and memoryos trace",
    },
    "skills": {
        "category": "agent-infra", "language": None,
        "url": "https://github.com/wesleymatosdev/skills.git", "public": True,
        "site": "https://skills.wesleymatos.dev",
        "description": "Personal agent-skill catalog, authored and battle-tested in real agent loops — skills.wesleymatos.dev",
    },
    "hermes-agent-rs": {
        "category": "library", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/hermes-agent-rs.git", "public": True,
        "description": "Composable Rust libraries and agent tools for integrating with Hermes Agent — typed API client, HMAC webhooks, orchestration",
    },
    "console-art": {
        "category": "library", "language": "JavaScript",
        "url": "https://github.com/wesleymatosdev/console-art.git", "public": False,
        "description": "Render colored ASCII art safely in the browser console — one console.log per row, bounded %c runs",
    },
    "aux-bench": {
        "category": "benchmark", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/aux-bench.git", "public": True,
        "description": "Benchmark local Ollama models for Hermes auxiliary task slots — scores measured behavior (empty-content failures), not vibes",
    },
    "ai-usage-optimizer": {
        "category": "agent-infra", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/ai-usage-optimizer.git", "public": True,
        "description": "Local-first usage tracker for AI subscriptions — polls real usage signals, Telegram alerts, recommends the provider with headroom",
    },
    "xcap-recorder": {
        "category": "cli-tool", "language": "Rust", "url": None, "public": True,
        "description": "Cross-platform screen recorder in Rust using xcap — records every display to a separate H.264 MP4 via FFmpeg",
    },
    "website": {
        "category": "website", "language": "HTML",
        "url": "https://github.com/wesleymatosdev/website.git", "public": False,
        "site": "https://wesleymatos.dev",
        "description": "Personal site at wesleymatos.dev — dark nebula theme with canvas starfield",
    },
    "blog": {
        "category": "website", "language": "Markdown", "url": None, "public": False,
        "site": "https://blog.wesleymatos.dev",
        "description": "Blog at blog.wesleymatos.dev — notes on code and things I'm building (Marmite)",
    },
    "demo": {
        "category": "website", "language": "HTML",
        "url": "https://github.com/wesleymatosdev/demo.git", "public": False,
        "site": "https://demo.wesleymatos.dev",
        "description": "Demos page for wesleymatos.dev",
    },
    "wm-brand": {
        "category": "website", "language": None, "url": None, "public": False,
        "description": "Design brief, tokens, and artifact previews for the wesleymatos.dev property family (HOUSE-STYLE.md defines the nebula language this site follows)",
    },
    "simulador-de-prova": {
        "category": "website", "language": "Svelte",
        "url": "https://github.com/wesleymatosdev/simulador-de-prova.git", "public": True,
        "description": "Exam simulator",
    },
    "spinning-cube": {
        "category": "experiment", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/spinning-cube.git", "public": True,
        "description": "Building a spinning cube to learn more about Rust",
    },
    "social-assets": {
        "category": "experiment", "language": None,
        "url": "https://github.com/wesleymatosdev/social-assets.git", "public": True,
        "description": "Public media assets referenced from social posts (LinkedIn, X, etc.), hosted via GitHub Releases for stable URLs",
    },
    "gnhf-lab": {
        "category": "experiment", "language": "Shell", "url": None, "public": False,
        "description": "Local experiment lab for gnhf — A/B agent lanes launched against personal repos",
    },
    "brainrs": {
        "category": "experiment", "language": "Markdown", "url": None, "public": True,
        "description": "Backlog spec for a Rust MEMORY_VERBS v1 server, measured against a running gbrain instance",
    },
    "drag-motion-spec-poc": {
        "category": "experiment", "language": "JavaScript", "url": None, "public": False,
        "description": "Drag-motion spec proof-of-concept with Playwright-verified proofs",
    },
    "skill-design-scratch": {
        "category": "experiment", "language": "Markdown", "url": None, "public": False,
        "description": "Scratch space for agent-skill design proposals",
    },
    "spike-semantic-tree": {
        "category": "experiment", "language": "Rust", "url": None, "public": False,
        "description": "Timeboxed research spike: semantic tree over Hermes sessions with real local embeddings (Rust)",
    },
    "memory-os": {
        "category": "contributions", "language": None,
        "url": "https://github.com/ClaudioDrews/memory-os", "public": True,
        "description": "Hermes Agent memory operating system — permanent local memory, provider-agnostic, with semantic search across conversations",
    },
    "colibri": {
        "category": "maintained-forks", "language": "C",
        "url": "https://github.com/wesleymatos-bot/colibri.git", "public": True,
        "description": "Run frontier MoE models on hardware you already own — pure C, zero deps, experts streamed from disk",
    },
    "gnhf": {
        "category": "maintained-forks", "language": None,
        "url": "https://github.com/wesleymatos-bot/gnhf.git", "public": True,
        "description": "Before I go to bed, I tell my agents: good night, have fun",
    },
    "fleet-bus": {
        "category": "agent-infra", "language": "Go", "url": None, "public": False,
        "description": "Low-latency push transport for the agent fleet — embedded NATS + JetStream, replayable history, one zero-dependency Go binary (v0.2)",
    },
    "oss-site": {
        "category": "website", "language": "HTML",
        "url": "https://github.com/wesleymatosdev/oss-site.git", "public": True,
        "description": "This catalog — source for oss.wesleymatos.dev; a hand-written static page fed by scripts/collect.py",
    },
    "terminal-axi": {
        "category": "cli-tool", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/terminal-axi.git", "public": True,
        "description": "Agent-ergonomic terminal session control — one Rust binary, one JSON contract, no daemon; run foreground or spawn detached and poll",
    },
    "zcode-axi": {
        "category": "cli-tool", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/zcode-axi.git", "public": True,
        "description": "Machine-friendly control plane around the zcode runtime — deterministic parseable output, documented exit-code contract, never prompts",
    },
    "zcode-cli": {
        "category": "contributions", "language": "Rust",
        "url": "https://github.com/kingsword09/zcode-cli", "public": True,
        "description": "Upstream zcode-cli — number-key quick-select for choice dialogs merged via PR #136; auto permission classifier under review as PR #137",
    },
}

# Local directory name -> catalog entry name (repo publishes under another name).
LOCAL_ALIAS = {
    "hermes-sdk": "hermes-agent-rs",   # remote is wesleymatosdev/hermes-agent-rs
    "demo-worker": "pages-proxy",      # remote is wesleymatosdev/pages-proxy
}

# Category for every non-fork repo taken from the API that has no curated entry.
API_CATEGORY = {
    "advent-of-code-2023": "experiment",
    "aoc-2024-in-deno": "experiment",
    "bela-portfolio": "website",
    "block-ads-huawei-router": "cli-tool",
    "bookstore-api": "experiment",
    "boilerplate": "experiment",
    "codespaces-test": "experiment",
    "data-structures-and-algorithms": "experiment",
    "deno-data-structures": "library",
    "deskflow-pentesting": "contributions",
    "exercism-rust": "experiment",
    "go-data-structures": "experiment",
    "go-movies-crud": "experiment",
    "hackerrank-with-go": "experiment",
    "hangman-game": "experiment",
    "hermes-classifier-mode": "agent-infra",
    "kafka-ecommerce": "experiment",
    "kafka-with-java": "experiment",
    "learning-rust": "experiment",
    "nu-auth": "experiment",
    "ologbonowiwii": "experiment",
    "pages-proxy": "cli-tool",
    "pi-hole-iac": "experiment",
    "poc-excel-download": "experiment",
    "proto-buffers": "experiment",
    "rinha-de-backend-rust": "experiment",
    "rinha-rust-warp": "experiment",
    "schedule-whatsapp-message-droideer": "experiment",
    "set-all-gists-to-private": "cli-tool",
    "simple-go-server": "experiment",
    "simple-node-demonstration": "experiment",
    "sort-numbers": "library",
    "taller-interview": "experiment",
    "the-divination-game": "experiment",
    "the-hangman-game": "experiment",
    "toggl-challenge": "experiment",
    "typescript-blockchain-implementation": "experiment",
    "voxy-challenge": "experiment",
    "wasm-example": "experiment",
    "web-rtc-video-call": "experiment",
    "what-is-the-weekday": "experiment",
}

# Descriptions for API repos whose GitHub description is null, derived from
# their READMEs (fetched when the curated table above doesn't cover them).
API_README_DESC = {
    "codespaces-test": "Quick node project template for demoing Codespaces",
    "hackerrank-with-go": "Go exercises from the HackerRank platform",
    "ologbonowiwii": "GitHub profile README",
    "toggl-challenge": "API that allows basic operations with a deck of french cards",
    "typescript-blockchain-implementation": "Simple algorithm based on Blockchain concepts, following @khaosdoctor's video",
}

# Language overrides where the API's dominant-language detection misleads
# (e.g. pages-proxy is a Rust worker that happens to ship a Makefile).
API_LANGUAGE_OVERRIDE = {
    "pages-proxy": "Rust",
    "unfit-rs": "Rust",
}

# Full per-project sections (rendered as large brief cards, not compact rows).
# Keys per entry: purpose (goals/what-it-does paragraph), state (short honest
# status label), state_note (optional caveat/evidence line). Copy sourced per
# entry in the plan §3; claims must stay true of the repo as it exists.
FULL_SECTIONS = {
    # --- agent-infra (8) ---
    "ai-usage-optimizer": {
        "purpose": ("Tracks real usage signals from the AI providers that expose them and "
                    "accepts manual observations for the ones that don't. On threshold "
                    "transitions it fires Telegram alerts and recommends which provider has "
                    "headroom for the next task. Local-first: provider keys are read from the "
                    "local environment and never leave it."),
        "state": "active", "state_note": None,
    },
    "anti-babysitting-pipeline": {
        "purpose": ("Support code for Hermes's autonomous Kanban supervisor. A read-only "
                    "SQLite monitor snapshots the board's cursor and status, so a cron "
                    "supervisor wakes only when the board actually changes — no polling loop "
                    "babysitting the queue."),
        "state": "working", "state_note": None,
    },
    "hermes-classifier-mode": {
        "purpose": ("A local LLM classifier reviews every shell command and execute_code "
                    "script before it runs inside Hermes Agent — autonomy with a second model "
                    "judging each action, instead of approval prompts or skipping all checks. "
                    "The ZCode sibling of auto-permissions; the same idea is proposed upstream "
                    "as kingsword09/zcode-cli PR #137."),
        "state": "working",
        "state_note": ("Accuracy and latency figures on the README are the project's own "
                       "benchmark self-report; no artifact is linked."),
    },
    "session-categorizer": {
        "purpose": ("Mines Hermes session databases with no model in the loop: deterministic "
                    "extraction of decisions, corrections, constraints, requests, blockers, "
                    "outcomes, open questions, ideas, and references — every extract carrying "
                    "a citation back to the source conversation."),
        "state": "working", "state_note": "39 test functions across 8 files.",
    },
    "skills": {
        "purpose": ("The agent-skill catalog behind skills.wesleymatos.dev: three skills with "
                    "a catalog.json in the agentskills.io schema and per-skill SHA-256 digests "
                    "in versions.json."),
        "state": "working", "state_note": None,
    },
    "usage-dash": {
        "purpose": ("A local, single-binary dashboard over the Hermes state DB: sessions, "
                    "model usage, provider load, and cost, straight out of SQLite. Read-only "
                    "by construction — the database opens in SQLite read-only mode; no agents "
                    "polled, no side effects."),
        "state": "working", "state_note": "22 unit tests; read-only access verified in src/metrics.rs.",
    },
    "fleet-bus": {
        "purpose": ("Low-latency push transport for the agent fleet: a worker finishing means "
                    "the coordinator knows in milliseconds, and any subscriber — including one "
                    "born after the events it cares about — can replay the history. v0.2 moves "
                    "the default path onto an embedded NATS server with JetStream while "
                    "staying one small zero-dependency Go binary."),
        "state": "working PoC — active",
        "state_note": ("Not published yet — repository is local-only; this entry links up "
                       "automatically once the repo is pushed."),
    },
    "auto-permissions": {
        "purpose": ("A ZCode plugin that adds a Claude-Code-style auto permission classifier: "
                    "known-safe actions are approved automatically, dangerous ones are denied "
                    "with a reason, and everything else goes to the normal human dialog. One "
                    "hook on PermissionRequest — it can never widen yolo mode or override an "
                    "explicit deny rule. The Hermes sibling is hermes-classifier-mode; the "
                    "same idea is under review upstream as kingsword09/zcode-cli PR #137."),
        "state": "working",
        "state_note": ("Not published yet — repository is local-only; this entry links up "
                       "automatically once the repo is pushed."),
    },
    # --- cli-tool (9) ---
    "ollama-axi": {
        "purpose": ("Maintenance CLI for a real Ollama store: `ollama rm` leaves blobs behind, "
                    "aborted pulls leave -partial files, and Ollama ships no cleanup command. "
                    "This tool reads the actual store and reclaims the dead weight — garbage "
                    "collection with a dry-run default, plus disk/list/ps inspection."),
        "state": "working", "state_note": "13 inline tests.",
    },
    "herdr-axi": {
        "purpose": ("AXI-discipline wrapper around the herdr agent multiplexer: list the live "
                    "agents, dispatch tasks to them, and wait until they reach a settled state "
                    "— machine-parsable output throughout, built to be driven by other agents "
                    "and scripts."),
        "state": "working",
        "state_note": "14 tests; brief derived from the code and Cargo.toml — the repo has no README yet.",
    },
    "scp-axi": {
        "purpose": ("Unattended file transfer to SSH-key-authenticated hosts: no interactive "
                    "prompts, ever; dry-run default for mutations; structured exit codes; human "
                    "and --json output. Host keys are pinned trust-on-first-use."),
        "state": "working",
        "state_note": ("23 tests plus CLI integration tests; the README documents the v0.1 "
                       "limits and the untested live-sshd path."),
    },
    "session-rc": {
        "purpose": ("Thin CLI to remote-control one exact live Hermes gateway session from a "
                    "phone — via Tailscale SSH/termux, or any shell with network access to the "
                    "gateway. A v0 slice of the \"control the live coordinator from my phone\" "
                    "idea."),
        "state": "v0 — working",
        "state_note": "The Tailscale path is documented in the README as not yet wired up.",
    },
    "xcap-recorder": {
        "purpose": ("Records every connected display into its own H.264 MP4 through FFmpeg, "
                    "built on the xcap capture library."),
        "state": "working — macOS only",
        "state_note": ("The FFmpeg encoder uses macOS's VideoToolbox (h264_videotoolbox) with "
                       "no fallback, so recording is macOS-only today even though the capture "
                       "core isn't platform-bound."),
    },
    "unfit-rs": {
        "purpose": ("Rust/axum rewrite of the unf.it review hub: local-first visual review of "
                    "websites with element-scoped feedback, comment threads, and SQLite "
                    "storage."),
        "state": "PoC — unmaintained",
        "state_note": "Superseded; the README recommends Lavish instead.",
    },
    "pages-proxy": {
        "purpose": ("A tiny Rust Cloudflare Worker that reverse-proxies a custom domain or "
                    "subdomain to a Cloudflare Pages project, preserving path and query "
                    "string. It serves demo.wesleymatos.dev."),
        "state": "working", "state_note": None,
    },
    "zcode-axi": {
        "purpose": ("Machine-friendly control plane around the zcode runtime: never prompts, "
                    "never opens the TUI, never touches login state. Deterministic, parseable "
                    "output only — compact one-line records by default, --json for whole "
                    "documents, --pretty for humans — with a documented exit-code contract for "
                    "machine callers."),
        "state": "active", "state_note": None,
    },
    "terminal-axi": {
        "purpose": ("Agent-ergonomic terminal session control: one small Rust binary, one "
                    "JSON contract, no daemon. Run a command in the foreground, or spawn it "
                    "detached and poll it like a real background session."),
        "state": "working", "state_note": None,
    },
    # --- library (2) ---
    "hermes-agent-rs": {
        "purpose": ("Composable Rust libraries and agent-facing tools for integrating with "
                    "and orchestrating Hermes Agent. Today that is the typed API client "
                    "hermes-client with HMAC webhook support; the README's status table "
                    "honestly marks the orchestrator and remaining crates as research or "
                    "planned."),
        "state": "v0.1 — hermes-client only", "state_note": None,
    },
    "console-art": {
        "purpose": ("Renders colored ASCII art safely in the browser console, chunking rows "
                    "so no single console.log exceeds the %c specifier cap. Unit tests plus a "
                    "browser-proof page and Bun leak-threshold tests."),
        "state": "working",
        "state_note": ("Source lives in a private repo, so there is no link here; the npm/JSR "
                       "package named in its README was never published."),
    },
    # --- benchmark (1) ---
    "aux-bench": {
        "purpose": ("Benchmarks local Ollama models for Hermes auxiliary task slots — title "
                    "generation, compression, curator, MCP, web extraction — scoring measured "
                    "behavior (such as empty-content failures) instead of vibes. Ships with a "
                    "REPRODUCING.md and committed run artifacts."),
        "state": "working PoC",
        "state_note": "14 result artifacts from real runs are committed under results/.",
    },
    # --- website (1) ---
    "website": {
        "purpose": ("wesleymatos.dev itself — the hand-written nebula/starfield home page "
                    "whose design language this catalog shares. The repository is private, so "
                    "there is no repo link; the live site is linked instead."),
        "state": "working", "state_note": None,
    },
}

# API repos deliberately absent from the catalog (silently skipped, no warning).
API_EXCLUDE = {
    "tmux-axi",  # 3-line cargo-new hello-world, no README — excluded until it has substance
}

# Local dirs deliberately absent from the catalog (walk never warns for these).
IGNORE_LOCAL = {
    "hermes-ops",       # OPSEC: maps the local Hermes secret topology (1Password paths,
                        # provider endpoints, relay topology) — zero visitor value.
    "unfit-madeline",   # STEER 9/11: names a private CLIENT in a public catalog; repo is
                        # private (dead link); deployed per-client instance of unfit,
                        # not Wesley's project. Never re-add; no client names in the catalog.
    "zcode-cli-pr",     # PR-staging clone — covered by the zcode-cli contributions row.
    "zcode-cli",        # upstream clone — covered by the zcode-cli contributions row.
    "tmux-axi",         # deliberately absent (see API_EXCLUDE); its local dir still exists,
                        # so the walk must not warn for it either.
    "orca-fork",        # upstream clone of stablyai/orca — not a Wesley project.
}


def api_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "oss-site-collector"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def local_repos():
    """Walk ~/projects/personal for git repos; return {dir_name: remote_or_None}."""
    repos = {}
    if not PERSONAL_DIR.is_dir():
        return repos
    for d in sorted(PERSONAL_DIR.iterdir()):
        if not (d / ".git").is_dir():
            continue
        try:
            remote = subprocess.run(
                ["git", "-C", str(d), "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip() or None
        except Exception:
            remote = None
        repos[d.name] = remote
    return repos


def main():
    repos = []
    for user in GITHUB_USERS:
        for r in api_get(f"https://api.github.com/users/{user}/repos?per_page=100"):
            if r["fork"] and r["name"] not in CURATED:
                continue  # forks are only listed when curated (colibri, gnhf)
            repos.append(r)

    entries = {}

    # Curated first: local/private repos with hand-derived descriptions.
    # url = the repo's existing remote, with a cosmetic ".git" stripped so
    # curated and API entries link the same way.
    local_walk = local_repos()
    for name, meta in CURATED.items():
        url = meta["url"]
        if url and url.endswith(".git"):
            url = url[: -len(".git")]
        entry = {
            "name": name,
            "description": meta["description"],
            "language": meta["language"],
            "url": url,
            "stars": None,
            "local": meta["url"] is None,
            "public": meta["public"],
            "site": meta.get("site"),
            "full": name in FULL_SECTIONS,
            "purpose": None,
            "state": None,
            "state_note": None,
            "category": meta["category"],
        }
        sec = FULL_SECTIONS.get(name)
        if sec:
            entry["purpose"] = sec["purpose"]
            entry["state"] = sec["state"]
            entry["state_note"] = sec["state_note"]
        entries[name] = entry

    # Then the API: enrich curated entries (stars), add the rest.
    for r in repos:
        name = r["name"]
        if name in entries:
            e = entries[name]
            e["stars"] = r["stargazers_count"]
            e["url"] = r["html_url"]   # backfill: heals stale local-only urls
            e["local"] = False
            e["public"] = True         # the API only lists public repos
            if e["description"] is None:
                e["description"] = r["description"]
        else:
            if name in API_EXCLUDE:
                continue
            category = API_CATEGORY.get(name)
            if category is None:
                print(f"WARNING: no category for API repo {name!r} — skipping. "
                      f"Add it to API_CATEGORY or CURATED in scripts/collect.py.")
                continue
            entries[name] = {
                "name": name,
                "description": r["description"] or API_README_DESC.get(name),
                "language": API_LANGUAGE_OVERRIDE.get(name, r["language"]),
                "url": r["html_url"],
                "stars": r["stargazers_count"],
                "local": False,
                "public": True,
                "site": None,
                "full": name in FULL_SECTIONS,
                "purpose": None, "state": None, "state_note": None,
                "category": category,
            }
            sec = FULL_SECTIONS.get(name)
            if sec:
                entries[name].update(purpose=sec["purpose"], state=sec["state"],
                                     state_note=sec["state_note"])

    # Sanity-check the local walk against the catalog.
    known = set(entries) | set(LOCAL_ALIAS)
    for dirname, remote in local_walk.items():
        if dirname in known or dirname in LOCAL_ALIAS.values() or dirname in IGNORE_LOCAL:
            continue
        if remote and any(remote.endswith(f"/{n}.git") or remote.endswith(f"/{n}")
                          for n in entries):
            continue
        print(f"WARNING: local repo {dirname!r} (remote {remote}) is not in the catalog.")

    data = {
        "generated": GENERATED,
        "source": "GitHub API (wesleymatosdev, wesleymatos-bot) + curated local walk of ~/projects/personal; regenerate with scripts/collect.py",
        "groups": [],
    }
    for gid, title, blurb in GROUPS:
        projects = sorted(
            (p for p in entries.values() if p["category"] == gid),
            key=lambda p: p["name"].lower(),
        )
        if not projects:
            continue
        data["groups"].append({"id": gid, "title": title, "blurb": blurb, "projects": projects})

    total = sum(len(g["projects"]) for g in data["groups"])

    out_json = REPO_ROOT / "data" / "projects.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    out_js = REPO_ROOT / "www" / "projects.js"
    out_js.parent.mkdir(parents=True, exist_ok=True)
    out_js.write_text(
        "// Generated by scripts/collect.py from data/projects.json — do not edit.\n"
        "window.OSS_PROJECTS = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"
    )

    lines = [
        "# wesley's open source",
        "> https://oss.wesleymatos.dev — catalog of Wesley Matos's open-source work.",
        f"> {total} projects, generated {GENERATED}. Groups: "
        + ", ".join(g["title"].lower() for g in data["groups"]) + ".",
        "",
    ]
    for g in data["groups"]:
        lines.append(f"## {g['title']}")
        lines.append("")
        for p in g["projects"]:
            if p["url"] and p["public"]:
                url = p["url"]
            elif p.get("site"):
                url = p["site"]
            elif p["local"]:
                url = "local only (coming soon)"
            else:
                url = "source not public"
            desc = p["description"] or ""
            lines.append(f"{p['name']} — {url} — {desc}")
        lines.append("")
    (REPO_ROOT / "www" / "llms.txt").write_text("\n".join(lines).rstrip() + "\n")

    print(f"OK: {total} projects across {len(data['groups'])} groups -> "
          f"{out_json}, {out_js}, www/llms.txt")


if __name__ == "__main__":
    main()
