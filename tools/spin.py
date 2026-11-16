#!/usr/bin/env python3
"""
spin.py: turn portrait.svg into portrait-spin.svg, a character-select turntable.

    python3 tools/spin.py [portrait.svg] [portrait-spin.svg]

The flat portrait turns clockwise about its vertical axis (scaleX = cos θ).
While it faces away, a flat pink silhouette stands in for the back. A glowing
platform ring sits under the feet. Pure SVG + SMIL, so it plays on GitHub.
"""
import math
import re
import sys

SECONDS = 8          # one full turn
STEPS = 48           # samples of cos θ for a smooth, even rotation


def main(src="portrait.svg", dst="portrait-spin.svg"):
    raw = open(src, encoding="utf-8").read()
    m = re.match(r'<svg[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>(.*)</svg>\s*$', raw, re.S)
    w, h, inner = float(m.group(1)), float(m.group(2)), m.group(3)
    style = re.search(r"<style>.*?</style>", inner, re.S).group(0)
    body = inner.replace(style, "")

    cx = w / 2
    plat_y = h + 14
    H = h + 44
    scales = ";".join(f"{math.cos(2 * math.pi * i / STEPS):.4f} 1" for i in range(STEPS + 1))
    # front shows for the first and last quarter turn, the back in between
    vis_front = 'values="1;0;1" keyTimes="0;0.25;0.75" calcMode="discrete"'
    vis_back = 'values="0;1;0" keyTimes="0;0.25;0.75" calcMode="discrete"'
    dur = f'dur="{SECONDS}s" repeatCount="indefinite"'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {H}" width="{w}" height="{H}" role="img" aria-label="Character-art portrait, slowly turning like a character select screen">{style}
<defs>
  <g id="art">{body}</g>
  <filter id="back" x="0" y="0" width="100%" height="100%">
    <feFlood flood-color="#8a2e46"/><feComposite in2="SourceAlpha" operator="in"/>
  </filter>
  <radialGradient id="glow"><stop offset="0" stop-color="#dd2d51" stop-opacity=".45"/><stop offset="1" stop-color="#dd2d51" stop-opacity="0"/></radialGradient>
</defs>
<ellipse cx="{cx}" cy="{plat_y}" rx="{w * 0.36:.1f}" ry="22" fill="url(#glow)"/>
<ellipse cx="{cx}" cy="{plat_y}" rx="{w * 0.30:.1f}" ry="14" fill="none" stroke="#dd2d51" stroke-width="1.5" opacity=".7"/>
<ellipse cx="{cx}" cy="{plat_y}" rx="{w * 0.30:.1f}" ry="14" fill="none" stroke="#dd2d51" stroke-width="1">
  <animate attributeName="rx" values="{w * 0.30:.1f};{w * 0.40:.1f}" {dur.replace(str(SECONDS) + "s", str(SECONDS / 4) + "s")}/>
  <animate attributeName="ry" values="14;22" {dur.replace(str(SECONDS) + "s", str(SECONDS / 4) + "s")}/>
  <animate attributeName="opacity" values=".8;0" {dur.replace(str(SECONDS) + "s", str(SECONDS / 4) + "s")}/>
</ellipse>
<g transform="translate({cx} 0)">
  <g>
    <animateTransform attributeName="transform" type="scale" values="{scales}" {dur}/>
    <g transform="translate({-cx} 0)">
      <use xlink:href="#art" href="#art">
        <animate attributeName="opacity" {vis_front} {dur}/>
      </use>
      <use xlink:href="#art" href="#art" filter="url(#back)" opacity="0">
        <animate attributeName="opacity" {vis_back} {dur}/>
      </use>
    </g>
  </g>
</g>
</svg>'''
    open(dst, "w", encoding="utf-8").write(svg)
    print(f"wrote {dst} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main(*sys.argv[1:])
