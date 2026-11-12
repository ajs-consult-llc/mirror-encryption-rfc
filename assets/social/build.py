#!/usr/bin/env python3
"""Draw the Cloud Data Mirror graphic and render it.

    python3 assets/social/build.py

Writes, next to this file:
  cloud-data-mirror.svg         the vector source, transparent
  cloud-data-mirror.png         1200x630, transparent: the site and the sign-up form
  cloud-data-mirror-social.png  1200x630 on white: the link preview (a transparent preview
                                    can look broken on dark-mode feeds)
  cloud-data-mirror-banner.png  1200x290, transparent: only the diagram band, for the sign-up
                                    form, which already shows the title and must fit one screen

Needs rsvg-convert (brew install librsvg). One accent colour, gold only for the user's key.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
INK, ACCENT, MUTED, GOLD = "#1f2933", "#2f5f86", "#5f7183", "#c8932e"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

# Each symbol is drawn around (0, 0), about 32 units across, in the ink stroke.
ICONS = {
    "mail": '<rect x="-16" y="-11" width="32" height="22" rx="3"/><polyline points="-15,-8 0,3 15,-8"/>',
    "messages": '<rect x="-16" y="-12" width="32" height="21" rx="6"/><path d="M-9 9 v7 l7 -7"/>',
    "calendar": ('<rect x="-15" y="-11" width="30" height="25" rx="3"/><line x1="-15" y1="-2" x2="15" y2="-2"/>'
                 '<line x1="-7" y1="-15" x2="-7" y2="-7"/><line x1="7" y1="-15" x2="7" y2="-7"/>'),
    "contacts": '<circle cx="0" cy="-6" r="6"/><path d="M-11 13 a11 9 0 0 1 22 0"/>',
    "wearable": ('<rect x="-9" y="-11" width="18" height="22" rx="5"/><path d="M-6 -11 v-6 h12 v6 M-6 11 v6 h12 v-6"/>'
                 '<polyline points="-6,0 -3,0 -1,-4 2,4 4,0 6,0"/>'),
    "machine": ('<path d="M-16 14 V-1 l8 -5 v5 l8 -5 v5 l7 -4 V-14 h7 v28 Z"/><line x1="-18" y1="14" x2="18" y2="14"/>'
                '<path d="M8 -19 a5 5 0 0 1 10 0"/>'),
    "answers": ('<rect x="-16" y="-12" width="32" height="21" rx="6"/><path d="M-9 9 v7 l7 -7"/>'
                f'<path d="M0 -8 C0.7 -3.5 1.5 -2.7 6 -2 C1.5 -1.3 0.7 -0.5 0 4 C-0.7 -0.5 -1.5 -1.3 -6 -2 '
                f'C-1.5 -2.7 -0.7 -3.5 0 -8 Z" fill="{INK}" stroke="none"/>'),
    "search": '<circle cx="-4" cy="-4" r="9"/><line x1="3" y1="3" x2="13" y2="13"/>',
    "summaries": ('<rect x="-11" y="-15" width="22" height="30" rx="3"/><line x1="-6" y1="-7" x2="6" y2="-7"/>'
                  '<line x1="-6" y1="-1" x2="6" y2="-1"/><line x1="-6" y1="5" x2="2" y2="5"/>'),
    "insights": ('<line x1="-15" y1="13" x2="15" y2="13"/><rect x="-12" y="1" width="6" height="10" rx="1"/>'
                 '<rect x="-3" y="-5" width="6" height="16" rx="1"/><rect x="6" y="-11" width="6" height="22" rx="1"/>'),
    "agents": f'<path d="M3 -16 L-8 2 H0 L-3 16 L8 -2 H0 Z" fill="{INK}" stroke="none"/>',
    "alerts": '<path d="M-10 6 h20 l-3 -4 v-7 a7 7 0 0 0 -14 0 v7 z"/><circle cx="0" cy="10" r="2.5"/>',
}
LEFT = [["mail", "messages", "calendar"], ["contacts", "wearable", "machine"]]
RIGHT = [["answers", "search", "summaries"], ["insights", "agents", "alerts"]]
TILE, GAP, ROW_TOPS = 64, 16, (282, 362)


def grid(x0: int, rows: list[list[str]]) -> str:
    out = []
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            x, y = x0 + c * (TILE + GAP), ROW_TOPS[r]
            cx, cy = x + TILE // 2, y + TILE // 2
            out.append(f'<rect x="{x}" y="{y}" width="{TILE}" height="{TILE}" rx="14" fill="{ACCENT}" '
                       f'fill-opacity="0.07" stroke="{ACCENT}" stroke-opacity="0.25" stroke-width="1.5"/>')
            out.append(f'<g transform="translate({cx},{cy})" fill="none" stroke="{INK}" stroke-width="2.25" '
                       f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')
    return "\n    ".join(out)


def svg() -> str:
    left_x, right_x = 110, 1200 - 110 - (3 * TILE + 2 * GAP)
    left_mid, right_mid = left_x + (3 * TILE + 2 * GAP) // 2, right_x + (3 * TILE + 2 * GAP) // 2
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="Cloud Data Mirror RFC, a security reference architecture open for comment: your data, encrypted with your key, readable only by the AI you approve">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0 0L10 5L0 10z" fill="{ACCENT}"/>
    </marker>
  </defs>
  <g font-family="{FONT}">
    <text x="600" y="78" text-anchor="middle" font-size="16" font-weight="700" letter-spacing="3" fill="{ACCENT}">SECURITY REFERENCE ARCHITECTURE</text>
    <text x="600" y="142" text-anchor="middle" font-size="48" font-weight="700" fill="{INK}">Cloud Data Mirror RFC</text>
    <text x="600" y="184" text-anchor="middle" font-size="22" fill="{MUTED}">Encrypted with your key. Readable only by the AI you approve.</text>

    {grid(left_x, LEFT)}
    {grid(right_x, RIGHT)}

    <line x1="{left_x + 3 * TILE + 2 * GAP + 18}" y1="354" x2="510" y2="354" stroke="{ACCENT}" stroke-width="2.5" marker-end="url(#arrow)"/>
    <line x1="690" y1="354" x2="{right_x - 18}" y2="354" stroke="{ACCENT}" stroke-width="2.5" marker-end="url(#arrow)"/>
    <g fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round">
      <circle cx="757" cy="336" r="6"/><line x1="763" y1="336" x2="777" y2="336"/><line x1="773" y1="336" x2="773" y2="342"/>
    </g>

    <path d="M600 236 L680 266 V330 C680 392 645 432 600 452 C555 432 520 392 520 330 V266 Z" fill="{ACCENT}" fill-opacity="0.08" stroke="{ACCENT}" stroke-width="3" stroke-linejoin="round"/>
    <path d="M584 340 v-16 a16 16 0 0 1 32 0 v16" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>
    <rect x="570" y="336" width="60" height="46" rx="10" fill="{INK}"/>
    <circle cx="600" cy="354" r="6" fill="#ffffff"/>
    <rect x="597.5" y="354" width="5" height="14" rx="2" fill="#ffffff"/>
    <g fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round">
      <circle cx="580" cy="412" r="9"/><line x1="589" y1="412" x2="624" y2="412"/><line x1="617" y1="412" x2="617" y2="421"/><line x1="608" y1="412" x2="608" y2="419"/>
    </g>

    <g font-size="19" font-weight="600" fill="{INK}" text-anchor="middle">
      <text x="{left_mid}" y="482">Your data</text>
      <text x="600" y="482">Encrypted with your key</text>
      <text x="{right_mid}" y="482">AI you approve</text>
    </g>

    <text x="600" y="566" text-anchor="middle" font-size="16" fill="{MUTED}">Published for open review by AJS Consult LLC</text>
    <text x="600" y="592" text-anchor="middle" font-size="16" fill="{ACCENT}">ajs-consult-llc.github.io/mirror-encryption-rfc</text>
  </g>
</svg>
'''


def render(src: Path, out: str, height: int, extra: list[str]) -> None:
    subprocess.run(["rsvg-convert", "-w", "1200", "-h", str(height), *extra, str(src), "-o", str(HERE / out)], check=True)


def main() -> None:
    full = svg()
    src = HERE / "cloud-data-mirror.svg"
    src.write_text(full, encoding="utf-8")
    render(src, "cloud-data-mirror.png", 630, [])
    render(src, "cloud-data-mirror-social.png", 630, ["--background-color=white"])
    # The banner is the same drawing, framed to the diagram band: one source, so it cannot drift.
    banner = HERE / "cloud-data-mirror-banner.svg"
    banner.write_text(full.replace('width="1200" height="630" viewBox="0 0 1200 630"',
                                   'width="1200" height="290" viewBox="0 214 1200 290"', 1), encoding="utf-8")
    render(banner, "cloud-data-mirror-banner.png", 290, [])
    print("wrote the svg sources and the full, social and banner PNGs")


if __name__ == "__main__":
    main()
