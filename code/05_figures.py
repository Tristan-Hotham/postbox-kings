"""Step 5. Static figures for the paper (release/paper/f_*.png) and the blog post (release/blog/b_*.png).

Maps are drawn from coordinates with a Natural Earth coastline (data/coast_ne10m.json); no web tiles. Every value
comes from data/results.json, data/postboxes.csv, data/towns.csv, data/towns_1911_check.csv and data/coverage_grid.csv.
Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono), as for the header.
Run: FONT_DIR=/path/to/fonts python3 code/05_figures.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "")
if FD:
    for f in ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf"]:
        fm.fontManager.addfont(os.path.join(FD, f))
    plt.rcParams["font.family"] = "IBM Plex Mono"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
B = pd.read_csv(os.path.join(ROOT, "data", "postboxes.csv"), usecols=["lat", "lon", "reign"])
T = pd.read_csv(os.path.join(ROOT, "data", "towns.csv"))
V = pd.read_csv(os.path.join(ROOT, "data", "towns_1911_check.csv"))
G = pd.read_csv(os.path.join(ROOT, "data", "coverage_grid.csv"))
COAST = json.load(open(os.path.join(ROOT, "data", "coast_ne10m.json")))
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog")
os.makedirs(PO, exist_ok=True); os.makedirs(BO, exist_ok=True)
FG, MUT, RULE, LAND, EDGE = "#1F1B18", "#6B6359", "#DDD4C3", "#E9E2D3", "#C9BCA4"
COL = {r["code"]: r["colour"] for r in R["reigns"]}
COL["untagged"] = "#C9C0B0"
K = np.cos(np.radians(54.5))


def style(ax, grid="x"):
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUT)
    ax.tick_params(colors=FG, length=0)
    if grid: ax.grid(axis=grid, color=RULE, lw=.8); ax.set_axisbelow(True)


def save(fig, name, blog):
    if blog:
        fig.savefig(os.path.join(BO, f"b_{name}.png"), dpi=160, facecolor=fig.get_facecolor())
    else:
        fig.savefig(os.path.join(PO, f"f_{name}.png"), dpi=200, facecolor="white")
    plt.close(fig)


def land(ax):
    for g in COAST:
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            a = np.array(poly[0])
            if a[:, 0].min() > 1.8: continue
            ax.add_patch(Polygon(np.c_[a[:, 0] * K, a[:, 1]], closed=True, fc=LAND, ec=EDGE, lw=.5))
    ax.set_xlim(-8.4 * K, 1.9 * K); ax.set_ylim(49.85, 60.9); ax.set_aspect(1); ax.axis("off")


def fig_map(blog):
    w = 9.5 if blog else 6.6
    fig, ax = plt.subplots(figsize=(w, w * 1.18), facecolor="#F6F1E7" if blog else "white")
    land(ax)
    a = B[~B.reign.isin(["VR", "EVIIR", "EVIIIR"])]
    ax.scatter(a.lon * K, a.lat, s=.25 if not blog else .4, c="#B9AE9C", lw=0, alpha=.5, rasterized=True)
    for c, s, al in (("EVIIR", 2.2, .6), ("VR", 3.0, .75)):
        d = B[B.reign == c]; ax.scatter(d.lon * K, d.lat, s=s * (1.5 if blog else 1), c=COL[c], lw=0, alpha=al, rasterized=True, label=None)
    d = B[B.reign == "EVIIIR"]
    ax.scatter(d.lon * K, d.lat, s=26 if blog else 14, c=COL["EVIIIR"], edgecolors=FG, lw=.5, zorder=5)
    fs = 12 if blog else 8
    items = [("#B9AE9C", f"all other boxes ({R['meta']['n'] - R['victoria']['n'] - R['reigns'][1]['n'] - R['edward8']['n']:,})"),
             (COL["VR"], f"Victoria, VR ({R['victoria']['n']:,})"), (COL["EVIIR"], f"Edward VII, EVIIR ({R['reigns'][1]['n']:,})"),
             (COL["EVIIIR"], f"Edward VIII, EVIIIR ({R['edward8']['n']})")]
    for i, (c, l) in enumerate(items):
        y = 60.55 - i * .32
        ax.scatter([-8.15 * K], [y], s=60 if blog else 30, c=c, edgecolors=FG if "VIII" in l else "none", lw=.5)
        ax.text(-7.9 * K, y, l, va="center", fontsize=fs, color=FG)
    ax.text(-8.2 * K, 59.15, f"UK post boxes in OpenStreetMap,\n{R['meta']['retrieved_text']}", fontsize=fs - 1, color=MUT, va="top")
    fig.subplots_adjust(0, 0, 1, 1)
    save(fig, "map", blog)


def fig_reigns(blog):
    rs = R["reigns"]
    if blog:
        for key, name, lab in (("n", "reigns", "Mapped post boxes"), ("per_year", "peryear", "Mapped boxes per year of reign")):
            fig, ax = plt.subplots(figsize=(9.5, 5.2), facecolor="#F6F1E7"); ax.set_facecolor("#F6F1E7")
            order = sorted(rs, key=lambda r: -r[key]) if key == "n" else rs
            y = np.arange(len(order))[::-1]
            ax.barh(y, [r[key] for r in order], color=[r["colour"] for r in order], height=.68)
            ax.set_yticks(y, [r["short"] for r in order], fontsize=13)
            mx = max(r[key] for r in order)
            for yy, r in zip(y, order): ax.text(r[key] + mx * .01, yy, f"{r[key]:,.0f}", va="center", fontsize=12, color=FG)
            ax.set_xlim(0, mx * 1.13); style(ax); ax.tick_params(axis="x", labelsize=11); ax.set_xlabel(lab, fontsize=12, color=MUT)
            fig.tight_layout(); save(fig, name, True)
        return
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.2))
    for ax, key, lab in ((axs[0], "n", "(a) Mapped boxes"), (axs[1], "per_year", "(b) Boxes per year of reign")):
        y = np.arange(len(rs))[::-1]
        ax.barh(y, [r[key] for r in rs], color=[r["colour"] for r in rs], height=.68, edgecolor=FG, lw=.3)
        ax.set_yticks(y, [r["short"] for r in rs] if key == "n" else [""] * len(rs), fontsize=7.5)
        mx = max(r[key] for r in rs)
        for yy, r in zip(y, rs): ax.text(r[key] + mx * .015, yy, f"{r[key]:,.0f}", va="center", fontsize=6.5)
        ax.set_xlim(0, mx * 1.25); style(ax); ax.tick_params(axis="x", labelsize=6.5); ax.set_title(lab, fontsize=8, loc="left")
    fig.tight_layout(); save(fig, "reigns", False)


def fig_types(blog):
    rs = R["reigns"]
    w, fs = (9.5, 13) if blog else (6.6, 7.5)
    fig, ax = plt.subplots(figsize=(w, w * .55), facecolor="#F6F1E7" if blog else "white")
    if blog: ax.set_facecolor("#F6F1E7")
    y = np.arange(len(rs))[::-1]; left = np.zeros(len(rs))
    cols = ["#C8102E", "#B85C1E", "#B08A1E", "#C9C0B0"]; hat = [None, "///", "...", None]
    for j, (k, lab) in enumerate((("pillar", "Pillar"), ("wall", "Wall"), ("lamp", "Lamp"), ("other_type", "Other or not recorded"))):
        v = np.array([r[k] / r["n"] for r in rs])
        ax.barh(y, v, left=left, color=cols[j], height=.66, label=lab, hatch=None if blog else hat[j], edgecolor="white", lw=.6)
        for yy, l, vv in zip(y, left, v):
            if vv > .09: ax.text(l + vv / 2, yy, f"{vv * 100:.0f}%", ha="center", va="center", fontsize=fs - 2, color="white" if j < 3 else FG)
        left += v
    ax.set_yticks(y, [r["short"] for r in rs], fontsize=fs); ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1], ["0%", "25%", "50%", "75%", "100%"], fontsize=fs - 2)
    style(ax, None); ax.legend(ncol=4, fontsize=fs - 2, frameon=False, loc="lower center", bbox_to_anchor=(.45, 1.0))
    fig.tight_layout(); save(fig, "types", blog)


def fig_towns(blog):
    t = T[(T.dated >= R["towns"]["min_dated"]) & (T.tagged_share >= R["towns"]["min_tagged"]) & T.pop2021.notna()]
    lab = {"Stevenage": (-6, 8, "right"), "Milton Keynes": (6, 8, "left"), "City and County of the City of London": (8, -2, "left"),
           "Royal Tunbridge Wells": (8, 0, "left"), "Cheltenham": (7, -3, "left")}
    if blog:
        fig, ax = plt.subplots(figsize=(9.5, 6), facecolor="#F6F1E7"); ax.set_facecolor("#F6F1E7"); fs = 12; axs = [ax]
    else:
        fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.1), gridspec_kw={"width_ratios": [1.6, 1]}); fs = 7; ax = axs[0]
    c = np.where(t.pre1910_share >= .25, COL["VR"], np.where(t.pre1936_share < .08, "#C8102E", "#8A8073"))
    ax.scatter(t.pop2021, t.pre1910_share * 100, s=40 if blog else 12, c=c, alpha=.8, edgecolors="white", lw=.5)
    ax.set_xscale("log"); ax.set_xlim(5000, 700000); ax.set_ylim(-2, 52)
    ax.set_xticks([1e4, 3e4, 1e5, 3e5], ["10k", "30k", "100k", "300k"]); ax.tick_params(labelsize=fs - 1)
    ax.set_xlabel("Census 2021 population (log scale)", fontsize=fs, color=MUT); ax.set_ylabel("Boxes from before 1910 (%)", fontsize=fs, color=MUT)
    for r in t.itertuples():
        if r.BUA22NM in lab:
            dx, dy, ha = lab[r.BUA22NM]
            ax.annotate(r.BUA22NM.split(" (")[0].replace("City and County of the ", ""), (r.pop2021, r.pre1910_share * 100), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=fs - 1, color=FG)
    style(ax, "y")
    if not blog:
        ax.set_title("(a) Towns in England and Wales", fontsize=8, loc="left")
        a2 = axs[1]
        a2.scatter(V.ratio * 100, V.pre1910 * 100, s=14, c="#8A8073", edgecolors=FG, lw=.3)
        for r in V.itertuples():
            if r.place in ("Bournemouth", "Aylesbury", "Bognor Regis", "Scarborough", "Tynemouth", "Blackpool"):
                a2.annotate(r.place, (r.ratio * 100, r.pre1910 * 100), xytext=(3, -9 if r.place == "Aylesbury" else 4), textcoords="offset points", fontsize=5.5)
        a2.set_xlabel("1911 population as % of 2021", fontsize=fs, color=MUT); a2.set_ylim(-2, 34); a2.tick_params(labelsize=fs - 1)
        a2.set_title(f"(b) {R['check1911']['n']} towns with a 1911 figure", fontsize=8, loc="left"); style(a2, "y")
    fig.tight_layout(); save(fig, "towns", blog)


def fig_cover(blog):
    tr = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    w = 9.5 if blog else 6.0
    fig, ax = plt.subplots(figsize=(w, w * 1.18), facecolor="#F6F1E7" if blog else "white")
    land(ax)
    cols = ["#B8432F", "#DE8A5A", "#E9C98E", "#8DB59A", "#2E7D4F"]
    g = G[G.n >= 5]
    for r in g.itertuples():
        xs = np.array([r.gx, r.gx + 1, r.gx + 1, r.gx]) * 20000; ys = np.array([r.gy, r.gy, r.gy + 1, r.gy + 1]) * 20000
        lo, la = tr.transform(xs, ys)
        s = r.share; ci = 0 if s < .25 else 1 if s < .5 else 2 if s < .75 else 3 if s < .9 else 4
        ax.add_patch(Polygon(np.c_[np.array(lo) * K, la], closed=True, fc=cols[ci], ec="white", lw=.3, alpha=.9))
    fs = 12 if blog else 8
    for i, l in enumerate(["under 25%", "25 to 49%", "50 to 74%", "75 to 89%", "90% or more"]):
        y = 60.5 - i * .3
        ax.add_patch(plt.Rectangle((-8.25 * K, y - .1), .17, .2, fc=cols[i])); ax.text(-7.8 * K, y, l, va="center", fontsize=fs, color=FG)
    ax.text(-8.25 * K, 60.85, f"Share of mapped boxes with a cypher tag\n({R['grid']['cell_km']} km squares with 5 or more boxes)", fontsize=fs - 1, color=MUT, va="bottom")
    fig.subplots_adjust(0, 0, 1, .97)
    save(fig, "cover", blog)


for blog in (False, True):
    fig_map(blog); fig_reigns(blog); fig_types(blog); fig_towns(blog); fig_cover(blog)
print("figures written")
