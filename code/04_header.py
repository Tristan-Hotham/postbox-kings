"""Step 4. Render header.png (1200x630 social card) with Playwright Chromium.

Fonts: FONT_DIR holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf
(from github.com/google/fonts); otherwise system serif is used. Coastline: data/coast_ne10m.json (Natural Earth, public domain).
Run: FONT_DIR=/path/to/fonts python3 code/04_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
BX = json.load(open(os.path.join(ROOT, "data", "boxes_page.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(54.5))
X0, X1, Y0, Y1 = -8.3 * K, 2.0 * K, -59.0, -49.9
Hh = 610; Ww = Hh * (X1 - X0) / (Y1 - Y0)
pr = lambda lat, lon: ((lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh)
land = ""
for g in json.load(open(os.path.join(ROOT, "data", "coast_ne10m.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in poly[0])) + "Z"
COL = {0: "#1F4E79", 1: "#7B3F98", 3: "#C9A227"}
dots = ""
for code, rr in ((1, 1.3), (0, 1.5), (3, 4.2)):
    for b in BX["rows"]:
        if b[2] != code: continue
        x, y = pr(b[0], b[1])
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr}" fill="{COL[code]}" fill-opacity="{.9 if code == 3 else .55}"{" stroke=\"#fff\" stroke-width=\".8\"" if code == 3 else ""}/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 50%,#FBF7EE 0%,#F6F1E7 55%,#E9E1D0 100%);color:#1F1B18;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:60px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#6B6359;display:flex;gap:12px;align-items:center}}
.k b{{background:#C8102E;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:64px;top:96px;margin:0;font:900 84px/.93 Fraunces,Georgia,serif;letter-spacing:-.02em;width:720px}}
h1 em{{font-style:normal;color:#C8102E}}
p{{position:absolute;left:70px;top:330px;width:640px;margin:0;font-size:25px;line-height:1.36}}
p b.v{{color:#1F4E79}} p b.e{{color:#9A7A10}}
.f{{position:absolute;left:70px;bottom:38px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#6B6359}}
svg{{position:absolute;right:26px;top:10px}}
.lg{{position:absolute;left:70px;bottom:70px;font:400 14px/1.6 'IBM Plex Mono',monospace;color:#6B6359;}}
.lg i{{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;vertical-align:-1px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Street furniture · 1853 to 2026</span></div>
<h1>What's the king on your <em>postbox?</em></h1>
<p>{R['meta']['n']:,} UK post boxes in OpenStreetMap. <b class="v">{R['victoria']['n']:,}</b> still carry Queen Victoria's VR; <b class="e">{R['edward8']['n']}</b> carry the cypher of Edward VIII, who reigned for 325 days.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E6DECD" stroke="#CDBFA6" stroke-width="1"/>{dots}</svg>
<div class="lg"><i style="background:#1F4E79"></i>Victoria &nbsp; <i style="background:#7B3F98"></i>Edward VII &nbsp; <i style="background:#C9A227"></i>Edward VIII</div>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(800)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
