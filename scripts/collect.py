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
    ("maintained-forks", "Maintained forks",
     "Forks kept alive with real work on them."),
    ("contributions", "Contributions",
     "Work done toward upstream projects."),
]

# Curated entries: local and/or private repos the public API can't describe.
# url is the repo's existing remote, exactly as configured; null = local only.
# local dirs that publish under a different GitHub name map via LOCAL_ALIAS.
CURATED = {
    "unfit": {
        "category": "website", "language": "HTML",
        "url": "https://github.com/wesleymatosdev/unfit.git",
        "description": "LAN-only review hub for visual artifacts — click-to-annotate DOM elements, queue comments, durable local SQLite storage",
    },
    "unfit-rs": {
        "category": "cli-tool", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/unfit-rs.git",
        "description": "unf.it review tool — Rust rewrite: local-first visual review hub for iterating on websites with element-scoped feedback",
    },
    "ollama-axi": {
        "category": "cli-tool", "language": "Rust", "url": None,
        "description": "Agent-grade model management for Ollama — gc orphaned blobs and aborted pulls, inspect the real store, reclaim dead weight",
    },
    "herdr-axi": {
        "category": "cli-tool", "language": "Rust", "url": None,
        "description": "AXI-discipline wrapper around the herdr multiplexer CLI",
    },
    "scp-axi": {
        "category": "cli-tool", "language": "Rust", "url": None,
        "description": "Unattended file transfer to SSH-key-authenticated hosts — no interactive prompts, dry-run default, human + --json output",
    },
    "tmux-axi": {
        "category": "cli-tool", "language": "Rust", "url": None,
        "description": "Small Rust CLI that wraps the tmux multiplexer with AXI discipline",
    },
    "session-rc": {
        "category": "cli-tool", "language": "Rust", "url": None,
        "description": "Thin CLI to remote-control one exact live Hermes gateway session from a phone",
    },
    "session-categorizer": {
        "category": "agent-infra", "language": "Python", "url": None,
        "description": "Deterministic, no-LLM categorizer for Hermes session databases — extracts decisions, constraints and blockers with citations",
    },
    "anti-babysitting-pipeline": {
        "category": "agent-infra", "language": "Shell", "url": None,
        "description": "Deterministic support code for Hermes's autonomous Kanban supervisor — wakes the supervisor only when the board changes",
    },
    "usage-dash": {
        "category": "agent-infra", "language": "Rust", "url": None,
        "description": "Read-only web dashboard over the local Hermes state DB and memoryos trace",
    },
    "skills": {
        "category": "agent-infra", "language": None,
        "url": "https://github.com/wesleymatosdev/skills.git",
        "description": "Personal agent-skill catalog, authored and battle-tested in real agent loops — skills.wesleymatos.dev",
    },
    "hermes-agent-rs": {
        "category": "library", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/hermes-agent-rs.git",
        "description": "Composable Rust libraries and agent tools for integrating with Hermes Agent — typed API client, HMAC webhooks, orchestration",
    },
    "console-art": {
        "category": "library", "language": "JavaScript",
        "url": "https://github.com/wesleymatosdev/console-art.git",
        "description": "Render colored ASCII art safely in the browser console — one console.log per row, bounded %c runs",
    },
    "aux-bench": {
        "category": "benchmark", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/aux-bench.git",
        "description": "Benchmark local Ollama models for Hermes auxiliary task slots — scores measured behavior (empty-content failures), not vibes",
    },
    "ai-usage-optimizer": {
        "category": "agent-infra", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/ai-usage-optimizer.git",
        "description": "Local-first usage tracker for AI subscriptions — polls real usage signals, Telegram alerts, recommends the provider with headroom",
    },
    "xcap-recorder": {
        "category": "cli-tool", "language": "Rust", "url": None,
        "description": "Cross-platform screen recorder in Rust using xcap — records every display to a separate H.264 MP4 via FFmpeg",
    },
    "website": {
        "category": "website", "language": "HTML",
        "url": "https://github.com/wesleymatosdev/website.git",
        "description": "Personal site at wesleymatos.dev — dark nebula theme with canvas starfield",
    },
    "blog": {
        "category": "website", "language": "Markdown", "url": None,
        "description": "Blog at blog.wesleymatos.dev — notes on code and things I'm building (Marmite)",
    },
    "demo": {
        "category": "website", "language": "HTML",
        "url": "https://github.com/wesleymatosdev/demo.git",
        "description": "Demos page for wesleymatos.dev",
    },
    "unfit-madeline": {
        "category": "website", "language": "Python",
        "url": "https://github.com/wesleymatosdev/unfit-madeline.git",
        "description": "unfit review-hub instance pairing a Python server with unfit-sdk.js",
    },
    "simulador-de-prova": {
        "category": "website", "language": "Svelte",
        "url": "https://github.com/wesleymatosdev/simulador-de-prova.git",
        "description": "Exam simulator",
    },
    "spinning-cube": {
        "category": "experiment", "language": "Rust",
        "url": "https://github.com/wesleymatosdev/spinning-cube.git",
        "description": "Building a spinning cube to learn more about Rust",
    },
    "social-assets": {
        "category": "experiment", "language": None,
        "url": "https://github.com/wesleymatosdev/social-assets.git",
        "description": "Public media assets referenced from social posts (LinkedIn, X, etc.), hosted via GitHub Releases for stable URLs",
    },
    "gnhf-lab": {
        "category": "experiment", "language": "Shell", "url": None,
        "description": "Local experiment lab for gnhf — A/B agent lanes launched against personal repos",
    },
    "brainrs": {
        "category": "experiment", "language": "Markdown", "url": None,
        "description": "Backlog spec for a Rust MEMORY_VERBS v1 server, measured against a running gbrain instance",
    },
    "drag-motion-spec-poc": {
        "category": "experiment", "language": "JavaScript", "url": None,
        "description": "Drag-motion spec proof-of-concept with Playwright-verified proofs",
    },
    "skill-design-scratch": {
        "category": "experiment", "language": "Markdown", "url": None,
        "description": "Scratch space for agent-skill design proposals",
    },
    "spike-semantic-tree": {
        "category": "experiment", "language": "Rust", "url": None,
        "description": "Timeboxed research spike: semantic tree over Hermes sessions with real local embeddings (Rust)",
    },
    "memory-os": {
        "category": "contributions", "language": None,
        "url": "https://github.com/ClaudioDrews/memory-os",
        "description": "Hermes Agent memory operating system — permanent local memory, provider-agnostic, with semantic search across conversations",
    },
    "colibri": {
        "category": "maintained-forks", "language": "C",
        "url": "https://github.com/wesleymatos-bot/colibri.git",
        "description": "Run frontier MoE models on hardware you already own — pure C, zero deps, experts streamed from disk",
    },
    "gnhf": {
        "category": "maintained-forks", "language": None,
        "url": "https://github.com/wesleymatos-bot/gnhf.git",
        "description": "Before I go to bed, I tell my agents: good night, have fun",
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
        entries[name] = {
            "name": name,
            "description": meta["description"],
            "language": meta["language"],
            "url": url,
            "stars": None,
            "local": meta["url"] is None,
            "category": meta["category"],
        }

    # Then the API: enrich curated entries (stars), add the rest.
    for r in repos:
        name = r["name"]
        if name in entries:
            entries[name]["stars"] = r["stargazers_count"]
            if entries[name]["description"] is None:
                entries[name]["description"] = r["description"]
            if name == "hermes-agent-rs":
                # local hermes-sdk dir publishes as hermes-agent-rs
                pass
        else:
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
                "category": category,
            }

    # Sanity-check the local walk against the catalog.
    known = set(entries) | set(LOCAL_ALIAS)
    for dirname, remote in local_walk.items():
        if dirname in known or dirname in LOCAL_ALIAS.values():
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
            url = p["url"] if p["url"] else "local only (coming soon)"
            desc = p["description"] or ""
            lines.append(f"{p['name']} — {url} — {desc}")
        lines.append("")
    (REPO_ROOT / "www" / "llms.txt").write_text("\n".join(lines).rstrip() + "\n")

    print(f"OK: {total} projects across {len(data['groups'])} groups -> "
          f"{out_json}, {out_js}, www/llms.txt")


if __name__ == "__main__":
    main()
