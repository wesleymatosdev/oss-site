#!/usr/bin/env python3
"""Maintain the shared wesleymatos.dev nav across the four hand-written sites.

The canonical nav markup lives here. Each site's index.html carries a
sentinel-delimited copy:

    <!-- wm-nav:begin ... -->
    <nav class="site-nav" aria-label="Sites"> ... </nav>
    <!-- wm-nav:end -->

This script regenerates that block in place, setting aria-current="page"
on the link matching the target site. First-time installation per site is
a manual edit (Phases 4-6 of the nav plan); this script only maintains
existing blocks and refuses files that have none.

The CSS sentinel block in each site's stylesheet is installed once by hand
and never touched here; per-site :root overrides also live outside the
sentinels for the same reason.

The blog is not spliced — Marmite renders its nav from the menu: key in
marmite.yaml; this script prints the equivalent YAML as a reminder.

Run by hand from oss-site:  python3 scripts/sync-nav.py [--no-oss]

  --no-oss    emit every copy WITHOUT the "Open Source" link (pre-DNS runs;
              the record for oss.wesleymatos.dev is Wesley's to create)
  --with-oss  include it (default)
"""

import re
import sys
from pathlib import Path

LINKS = [  # (label, url) in display order; the OSS link is DNS-gated
    ("Home", "https://wesleymatos.dev"),
    ("Blog", "https://blog.wesleymatos.dev"),
    ("Open Source", "https://oss.wesleymatos.dev"),
    ("Skills", "https://skills.wesleymatos.dev"),
    ("Demos", "https://demo.wesleymatos.dev"),
]
CURRENT = {  # target -> the link that is "here"
    "oss-site": "https://oss.wesleymatos.dev",
    "website": "https://wesleymatos.dev",
    "skills": "https://skills.wesleymatos.dev",
    "demo": "https://demo.wesleymatos.dev",
}
TARGETS = {  # target -> the file carrying the sentinel block
    "website": "~/projects/personal/website/www/index.html",
    "skills": "~/projects/personal/skills/www/index.html",
    "demo": "~/projects/personal/demo/index.html",
    "oss-site": "~/projects/personal/oss-site/www/index.html",
}
BLOG_MENU_YAML = """\
# blog is not spliced — add/refresh the menu: key in marmite.yaml instead
# (omit the Open Source line until the oss.wesleymatos.dev DNS record exists):
# menu:
#   - ["Home", "https://wesleymatos.dev"]
#   - ["Open Source", "https://oss.wesleymatos.dev"]   # DNS-gated
#   - ["Skills", "https://skills.wesleymatos.dev"]
#   - ["Demos", "https://demo.wesleymatos.dev"]
"""


def partial(current_href, include_oss=True):
    links = [(l, u) for l, u in LINKS if include_oss or u != "https://oss.wesleymatos.dev"]
    lines = []
    for label, url in links:
        cur = ' aria-current="page"' if url == current_href else ""
        lines.append(f'  <a href="{url}"{cur}>{label}</a>')
    lis = "\n".join(lines)
    return ("<!-- wm-nav:begin — shared wesleymatos.dev nav; "
            "edit via oss-site scripts/sync-nav.py only -->\n"
            f'<nav class="site-nav" aria-label="Sites">\n{lis}\n</nav>\n'
            "<!-- wm-nav:end -->")


def splice(path, current_href, include_oss):
    p = Path(path).expanduser()
    text = p.read_text()
    block = partial(current_href, include_oss)
    # match on the begin sentinel PREFIX — the installed comment may carry a suffix
    new, n = re.subn(r"<!-- wm-nav:begin\b.*?<!-- wm-nav:end -->",
                     lambda _: block, text, flags=re.S)
    if n != 1:
        sys.exit(f"ERROR: expected exactly one wm-nav block in {p}, found {n}")
    p.write_text(new)
    print(f"synced {p}: "
          f"{'with' if include_oss else 'without'} Open Source link")


def main(argv):
    include_oss = "--no-oss" not in argv
    if not include_oss and "--with-oss" in argv:
        sys.exit("ERROR: --no-oss and --with-oss are mutually exclusive")
    for target, path in TARGETS.items():
        splice(path, CURRENT[target], include_oss)
    print(BLOG_MENU_YAML, end="")


if __name__ == "__main__":
    main(sys.argv[1:])
