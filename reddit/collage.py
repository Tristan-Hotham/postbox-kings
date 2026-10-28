"""r/dataisbeautiful collage: reddit/whats_the_king_on_your_postbox.png (2400 x 3000), light cream and pillar-box red.
Every number comes from ../data/results.json and ../data/postboxes.csv. Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono).
Run from this folder: FONT_DIR=/path/to/fonts python3 collage.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, EDGE, HOT = "#F7F1E4", "#1F1B18", "#6B6359", "#E8DFCC", "#D2C5AC", "#C8102E"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
RD = {r["code"]: r for r in R["reigns"]}
COL = {c: RD[c]["colour"] for c in RD}
B = pd.read_csv(os.path.join(ROOT, "data", "postboxes.csv"), usecols=["lat", "lon", "reign"])
COAST = json.load(open(os.path.join(ROOT, "data", "coast_ne10m.json")))
K = np.cos(np.radians(54.5))


def land(ax, lw=.5):
    for g in COAST:
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            a = np.array(poly[0])
            if a[:, 0].min() > 1.8: continue
            ax.add_patch(Polygon(np.c_[a[:, 0] * K, a[:, 1]], closed=True, fc=LAND, ec=EDGE, lw=lw))


fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.045, 0.972, "What's the king on", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(0.045, 0.920, "your postbox?", fontproperties=DISP, fontsize=54, color=HOT, va="top")
fig.text(0.045, 0.862, f"Every British post box carries the cypher of the monarch who reigned when it was made. Volunteers\n"
         f"on OpenStreetMap have read it on {R['tag']['dated']:,} UK boxes. Each dot below is one of them, coloured by reign.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.1)

# hero map: every box with a known reign, in shuffled order so the colours show the real mix
ax = fig.add_axes([0.0, 0.29, 0.6, 0.545]); ax.set_facecolor(BG)
land(ax)
d = B[B.reign.isin(list(RD))].sample(frac=1, random_state=3)
ax.scatter(d.lon * K, d.lat, s=1.1, c=d.reign.map(COL), lw=0, alpha=.9, rasterized=True)
e8 = B[B.reign == "EVIIIR"]
ax.scatter(e8.lon * K, e8.lat, s=26, c=COL["EVIIIR"], edgecolors=FG, lw=.6, zorder=5)
ax.set_xlim(-8.3 * K, 1.9 * K); ax.set_ylim(49.9, 60.9); ax.set_aspect(1); ax.axis("off")
ax.annotate("Scotland: the Crown of Scotland\nreplaced EIIR after the\nPillar Box War of 1952 to 1953", xy=(-3.6 * K, 56.6), xytext=(-8.2 * K, 59.4),
            family=MONO, fontsize=10.5, color=FG, arrowprops=dict(arrowstyle="-", color=FG, lw=.8))

# legend with counts
lx = fig.add_axes([0.6, 0.615, 0.38, 0.19]); lx.axis("off"); lx.set_xlim(0, 1); lx.set_ylim(0, 1)
order = ["EIIR", "GR", "GVIR", "SC", "VR", "EVIIR", "EVIIIR", "CIIIR"]
for i, c in enumerate(order):
    y = .95 - i * .125
    lx.scatter([.03], [y], s=120, c=COL[c], edgecolors=FG if c == "EVIIIR" else "none", lw=.6)
    lx.text(.08, y, RD[c]["short"] + (" (ringed)" if c == "EVIIIR" else ""), family=MONO, fontsize=12.5, color=FG, va="center")
    lx.text(.70, y, f"{RD[c]['n']:,}", family=MONO, fontsize=12.5, color=FG, va="center", ha="right")
    lx.text(.74, y, RD[c]["span"], family=MONO, fontsize=10.5, color=MUT, va="center")

# headline numbers
tx = fig.add_axes([0.6, 0.30, 0.38, 0.30]); tx.axis("off"); tx.set_xlim(0, 1); tx.set_ylim(0, 1)
items = [
    (f"{R['edward8']['n']}", COL["EVIIIR"], f"boxes of Edward VIII, who reigned 325 days:\n{R['edward8']['share_of_lbsg'] * 100:.0f}% of the 171 survivors specialists know.\nPer year of reign, twice Victoria's rate."),
    (f"{R['victoria']['n']:,}", COL["VR"], f"Victorian VR boxes still mapped.\n{R['victoria']['wall']:,} of them are wall boxes, safe\nfrom passing traffic."),
    (f"{R['scotland']['sc_share_post52'] * 100:.0f}%", COL["SC"], f"of Scotland's post-1952 boxes carry the\ncrown, not EIIR: {R['scotland']['sc']:,} against {R['scotland']['eiir']}."),
    (f"{R['towns']['oldest'][0]['pre1910'] * 100:.0f}%", HOT, f"of the City of London's boxes are Victorian\nor Edwardian. Stevenage, Crawley and\nMilton Keynes: two or fewer each."),
]
for i, (big, c, txt) in enumerate(items):
    y = .99 - i * .25
    tx.text(0, y, big, fontproperties=DISP, fontsize=36, color=c, va="top")
    tx.text(0, y - .12, txt, family=SER, fontsize=12.5, color=FG, va="top", linespacing=1.05)

# small multiples: one map per reign
fig.text(0.045, 0.283, "ONE MAP PER REIGN", family=MONO, fontsize=11, color=MUT)
sm = ["VR", "EVIIR", "GR", "EVIIIR", "GVIR", "CIIIR"]
for i, c in enumerate(sm):
    a = fig.add_axes([0.01 + i * 0.163, 0.075, 0.16, 0.155]); a.set_facecolor(BG)
    land(a, lw=.2)
    s = B[B.reign == c]
    a.scatter(s.lon * K, s.lat, s=8 if c in ("EVIIIR", "CIIIR") else 1.4, c=COL[c], lw=0, alpha=.9, rasterized=True)
    a.set_xlim(-8.3 * K, 1.9 * K); a.set_ylim(49.9, 59.2); a.set_aspect(1); a.axis("off")
    fig.text(0.09 + i * 0.163, 0.252, RD[c]["short"], family=MONO, fontsize=12, color=FG, ha="center")
    fig.text(0.09 + i * 0.163, 0.237, f"{RD[c]['n']:,} boxes", family=MONO, fontsize=11, color=COL[c], ha="center")

fig.text(0.045, 0.058, f"Data: post boxes © OpenStreetMap contributors (ODbL), retrieved {R['meta']['retrieved_text']}; {R['tag']['untagged']:,} more mapped boxes have no cypher recorded,\n"
         "so these are mapped boxes, not all boxes. Edward VIII survivors: Letter Box Study Group, via Historic Environment Scotland.\n"
         "Towns: ONS 2022 built-up areas. Coastline: Natural Earth. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.25)
fig.savefig(os.path.join(HERE, "whats_the_king_on_your_postbox.png"), dpi=200, facecolor=BG)
print("collage written")
