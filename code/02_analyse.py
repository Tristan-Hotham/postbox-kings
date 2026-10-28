"""Step 2. Every statistic used on the page, in the paper, the blog post and the collage.

Input : work/boxes.pkl, work/bua.pkl, work/meta.json (step 1)
        /home/claude/hist/osnames_gb.tsv (OS Open Names: towns and villages for the nearest-box measures)
        /home/claude/hist/_data12/wd_osm_bundle12.json.gz, key wd_postboxes (Wikidata, CC0) for the cross-check
        /home/claude/hist/seaside-railways/data/places.csv (1911 census populations from A Vision of Britain through Time,
        collected for my seaside railways study) for the "street furniture as a clock" check
Output: data/results.json, data/reigns.csv, data/areas.csv, data/towns.csv, data/edward_viii.csv, data/coverage_grid.csv,
        data/boxes_page.json, data/places_search.json
Run: python3 code/02_analyse.py
"""
import gzip, io, json, os, re
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy import stats
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
OSN = "/home/claude/hist/osnames_gb.tsv"
BUNDLE = "/home/claude/hist/_data12/wd_osm_bundle12.json.gz"
SEASIDE = "/home/claude/hist/seaside-railways/data/places.csv"
B = pd.read_pickle(os.path.join(ROOT, "work", "boxes.pkl"))
BU = pd.read_pickle(os.path.join(ROOT, "work", "bua.pkl"))
META = json.load(open(os.path.join(ROOT, "work", "meta.json")))
R = {}

# ---------- reigns ----------
# Reign dates (standard): Victoria to 22 Jan 1901; Edward VII to 6 May 1910; George V to 20 Jan 1936; Edward VIII to 11 Dec 1936;
# George VI to 6 Feb 1952; Elizabeth II to 8 Sep 2022. Boxes: the first in mainland Britain was at Botchergate, Carlisle, in 1853
# (Wikipedia, "Pillar box"); the first Charles III box was unveiled on 12 July 2024 (same article). "Years of boxes" runs from
# the later of the reign start and those dates to the end of the reign (or the data date for Charles III).
RET = META["retrieved"]
yr = lambda y, m, d: y + (m - 1) / 12 + (d - 1) / 365.25
ret_y = yr(int(RET[:4]), int(RET[5:7]), int(RET[8:10]))
REIGNS = [
    ("VR", "Victoria", "Queen Victoria", "1837 to 1901", yr(1853, 1, 1), yr(1901, 1, 22), "#1F4E79"),
    ("EVIIR", "Edward VII", "King Edward VII", "1901 to 1910", yr(1901, 1, 22), yr(1910, 5, 6), "#7B3F98"),
    ("GR", "George V", "King George V", "1910 to 1936", yr(1910, 5, 6), yr(1936, 1, 20), "#2E7D4F"),
    ("EVIIIR", "Edward VIII", "King Edward VIII", "1936", yr(1936, 1, 20), yr(1936, 12, 11), "#C9A227"),
    ("GVIR", "George VI", "King George VI", "1936 to 1952", yr(1936, 12, 11), yr(1952, 2, 6), "#B85C1E"),
    ("EIIR", "Elizabeth II", "Queen Elizabeth II", "1952 to 2022", yr(1952, 2, 6), yr(2022, 9, 8), "#C8102E"),
    ("SC", "Scottish crown", "Crown of Scotland (Scottish boxes since 1953)", "1953 on", yr(1953, 1, 1), ret_y, "#3A5BA0"),
    ("CIIIR", "Charles III", "King Charles III", "2022 on", yr(2024, 7, 12), ret_y, "#5A2A82"),
]
DATED = [r[0] for r in REIGNS]
B["dated"] = B.reign.isin(DATED)
n = len(B); nd = int(B.dated.sum())
import datetime as _dt
R["meta"] = dict(retrieved=RET, retrieved_text=_dt.date.fromisoformat(RET).strftime("%-d %B %Y"), raw_rows=META["raw_rows"], n=n, nodes=int((B.kind == "node").sum()), ways=int((B.kind != "node").sum()),
                 rm_total=115000, rm_year=2002)
R["meta"]["osm_vs_rm"] = n / 115000
R["tag"] = dict(tagged=int((B.reign != "untagged").sum()), dated=nd, none=int((B.reign == "none").sum()),
                unclear=int((B.reign == "unclear").sum()), untagged=int((B.reign == "untagged").sum()))
R["tag"]["tagged_share"] = R["tag"]["tagged"] / n; R["tag"]["dated_share"] = nd / n
R["tag"]["untagged_share"] = R["tag"]["untagged"] / n
R["types"] = {t: int((B.btype == t).sum()) for t in ("pillar", "wall", "lamp", "other", "")}
rows = []
for code, short, full, span, y0, y1, col in REIGNS:
    s = B[B.reign == code]
    d = dict(code=code, short=short, name=full, span=span, colour=col, n=len(s), share=len(s) / nd, years=round(y1 - y0, 2),
             per_year=len(s) / (y1 - y0), pillar=int((s.btype == "pillar").sum()), wall=int((s.btype == "wall").sum()),
             lamp=int((s.btype == "lamp").sum()), other_type=int((~s.btype.isin(["pillar", "wall", "lamp"])).sum()),
             england=int((s.nation == "England").sum()), scotland=int((s.nation == "Scotland").sum()),
             wales=int((s.nation == "Wales").sum()), ni=int((s.nation == "Northern Ireland").sum()))
    rows.append(d)
R["reigns"] = rows
pd.DataFrame(rows).drop(columns="colour").to_csv(os.path.join(ROOT, "data", "reigns.csv"), index=False)
RD = {r["code"]: r for r in rows}
R["old"] = dict(pre1910=RD["VR"]["n"] + RD["EVIIR"]["n"], pre1936=RD["VR"]["n"] + RD["EVIIR"]["n"] + RD["GR"]["n"] + RD["EVIIIR"]["n"])
R["old"]["pre1910_share"] = R["old"]["pre1910"] / nd; R["old"]["pre1936_share"] = R["old"]["pre1936"] / nd
R["old"]["pre1952"] = R["old"]["pre1936"] + RD["GVIR"]["n"]; R["old"]["pre1952_share"] = R["old"]["pre1952"] / nd
R["old"]["vr_per_eii"] = RD["EIIR"]["n"] / RD["VR"]["n"]
R["old"]["per_year_ratio_eii_vr"] = RD["EIIR"]["per_year"] / RD["VR"]["per_year"]

# ---------- nations ----------
nat = []
for nm in ["England", "Scotland", "Wales", "Northern Ireland"]:
    s = B[B.nation == nm]; dd = s[s.dated]
    e = dict(nation=nm, n=len(s), tagged_share=float((s.reign != "untagged").mean()), dated=len(dd))
    for c in DATED: e[c] = int((dd.reign == c).sum())
    e["vr_share"] = e["VR"] / max(1, len(dd)); e["pre1910_share"] = (e["VR"] + e["EVIIR"]) / max(1, len(dd))
    nat.append(e)
R["nations"] = nat
NT = {e["nation"]: e for e in nat}

# ---------- Scotland and the Pillar Box War ----------
sco = B[(B.nation == "Scotland") & B.dated]
R["scotland"] = dict(sc=int((sco.reign == "SC").sum()), eiir=int((sco.reign == "EIIR").sum()), ciiir=int((sco.reign == "CIIIR").sum()),
                     sc_outside=int(((B.reign == "SC") & (B.nation != "Scotland")).sum()))
R["scotland"]["sc_outside_border"] = int(((B.reign == "SC") & (B.nation != "Scotland") & (B.lat > 55.55)).sum())
R["scotland"]["sc_share_post52"] = R["scotland"]["sc"] / (R["scotland"]["sc"] + R["scotland"]["eiir"] + R["scotland"]["ciiir"])
R["scotland"]["eiir_types"] = {t: int(((sco.reign == "EIIR") & (sco.btype == t)).sum()) for t in ("pillar", "wall", "lamp")}
R["scotland"]["sc_types"] = {t: int(((sco.reign == "SC") & (sco.btype == t)).sum()) for t in ("pillar", "wall", "lamp")}

# ---------- Edward VIII ----------
E8 = B[B.reign == "EVIIIR"].copy()
E8["place"] = np.where(E8.near_town_km < 3, E8.near_town, E8.near_place)
e8 = E8[["osm", "lat", "lon", "btype", "design", "nation", "area", "near_place", "near_town", "place"]].sort_values(["nation", "area", "place"])
e8.assign(lat=e8.lat.round(5), lon=e8.lon.round(5)).drop(columns="place").to_csv(os.path.join(ROOT, "data", "edward_viii.csv"), index=False)
R["edward8"] = dict(n=len(E8), pillar=int((E8.btype == "pillar").sum()), wall=int((E8.btype == "wall").sum()),
                    lamp=int((E8.btype == "lamp").sum()), other=int((~E8.btype.isin(["pillar", "wall", "lamp"])).sum()),
                    england=int((E8.nation == "England").sum()), scotland=int((E8.nation == "Scotland").sum()),
                    wales=int((E8.nation == "Wales").sum()), ni=int((E8.nation == "Northern Ireland").sum()),
                    made=271, made_pillar=161, lbsg_surviving=171)
R["edward8"]["share_of_lbsg"] = len(E8) / 171
top8 = E8.area.value_counts()
R["edward8"]["top_areas"] = [dict(area=a, n=int(v)) for a, v in top8.head(8).items()]
lon8 = E8[E8.area.isin(["Greater London"]) | E8.area.str.contains("London", na=False)]
R["edward8"]["london"] = len(lon8)
R["edward8"]["list"] = [dict(place=r.place, area=r.area, nation=r.nation, type=r.btype or "not tagged", lat=round(r.lat, 5), lon=round(r.lon, 5), osm=r.osm)
                        for r in e8.itertuples()]

# ---------- Victoria and Penfolds ----------
VR = B[B.reign == "VR"]
R["victoria"] = dict(n=len(VR), pillar=int((VR.btype == "pillar").sum()), wall=int((VR.btype == "wall").sum()), lamp=int((VR.btype == "lamp").sum()))
pf = B[B.penfold != ""]
R["penfold"] = dict(original=int((B.penfold == "original").sum()), replica=int((B.penfold == "replica").sum()),
                    original_vr=int(((B.penfold == "original") & (B.reign == "VR")).sum()),
                    replica_sc=int(((B.penfold == "replica") & (B.reign == "SC")).sum()),
                    wiki_made=300, wiki_survive=150, wiki_replicas=100)
po = B[B.penfold == "original"]
R["penfold"]["original_scotland"] = int((po.nation == "Scotland").sum()); R["penfold"]["original_ni"] = int((po.nation == "Northern Ireland").sum())
R["penfold"]["replica_vr"] = int(((B.penfold == "replica") & (B.reign == "VR")).sum())
R["victoria"]["replica"] = R["penfold"]["replica_vr"]; R["victoria"]["genuine"] = R["victoria"]["n"] - R["penfold"]["replica_vr"]
R["designs"] = {d: {c: int(v) for c, v in B[B.design == d].reign.value_counts().items()} for d in ("fluted", "octagonal", "hovis", "ludlow", "waggon_top")}
R["penfold"]["top_areas"] = [dict(area=a, n=int(v)) for a, v in po.area.value_counts().head(6).items()]
R["penfold"]["share_of_wiki"] = R["penfold"]["original"] / 150

# ---------- areas (OS Open Names county or unitary/metropolitan district) ----------
A = B.groupby("area").agg(n=("osm", "size"), tagged=("reign", lambda r: int((r != "untagged").sum())), dated=("dated", "sum"),
                          nation=("nation", lambda s: s.mode().iloc[0]), lat=("lat", "median"), lon=("lon", "median"),
                          **{c: ("reign", (lambda c: (lambda r: int((r == c).sum())))(c)) for c in DATED})
A["tagged_share"] = A.tagged / A.n
A["vr_share"] = A.VR / A.dated.clip(lower=1)
A["pre1910_share"] = (A.VR + A.EVIIR) / A.dated.clip(lower=1)
A = A.reset_index()
A.round(4).to_csv(os.path.join(ROOT, "data", "areas.csv"), index=False)
R["areas"] = dict(n=len(A), vr_top=[dict(area=r.area, nation=r.nation, VR=int(r.VR), dated=int(r.dated), share=float(r.vr_share)) for r in A.sort_values("VR", ascending=False).head(12).itertuples()],
                  vr_share_top=[dict(area=r.area, nation=r.nation, VR=int(r.VR), dated=int(r.dated), share=float(r.vr_share)) for r in A[A.dated >= 300].sort_values("vr_share", ascending=False).head(10).itertuples()],
                  tag_top=[dict(area=r.area, n=int(r.n), share=float(r.tagged_share)) for r in A[A.n >= 300].sort_values("tagged_share", ascending=False).head(8).itertuples()],
                  tag_bottom=[dict(area=r.area, n=int(r.n), share=float(r.tagged_share)) for r in A[A.n >= 300].sort_values("tagged_share").head(8).itertuples()])
big = A[A.n >= 300]
R["areas"]["n_big"] = len(big)
R["areas"]["big_tag_median"] = float(big.tagged_share.median())
R["areas"]["big_tag_ge90"] = int((big.tagged_share >= .9).sum()); R["areas"]["big_tag_lt50"] = int((big.tagged_share < .5).sum())
R["areas"]["big_tag_min"] = float(big.tagged_share.min()); R["areas"]["big_tag_max"] = float(big.tagged_share.max())

# ---------- does tagging favour old boxes? reign mix in well-surveyed areas ----------
well = big[big.tagged_share >= .9].area
W = B[B.area.isin(well) & B.dated]
R["bias"] = dict(areas=int(len(well)), dated=len(W), vr_share=float((W.reign == "VR").mean()),
                 pre1910_share=float(W.reign.isin(["VR", "EVIIR"]).mean()), pre1936_share=float(W.reign.isin(["VR", "EVIIR", "GR", "EVIIIR"]).mean()),
                 all_vr_share=RD["VR"]["share"], all_pre1910_share=R["old"]["pre1910_share"], all_pre1936_share=R["old"]["pre1936_share"])
poorly = big[big.tagged_share < .6].area
Wp = B[B.area.isin(poorly) & B.dated]
R["bias"]["poor_areas"] = int(len(poorly)); R["bias"]["poor_dated"] = len(Wp)
R["bias"]["poor_vr_share"] = float((Wp.reign == "VR").mean()) if len(Wp) else None
R["bias"]["poor_pre1936_share"] = float(Wp.reign.isin(["VR", "EVIIR", "GR", "EVIIIR"]).mean()) if len(Wp) else None
rho = stats.spearmanr(big.tagged_share, big.pre1910_share)
R["bias"]["rho_tag_old"] = float(rho.statistic); R["bias"]["p_tag_old"] = float(rho.pvalue)

# ---------- coverage grid (20 km squares on the British National Grid) ----------
CELL = 20000
B["gx"] = (B.x // CELL).astype(int); B["gy"] = (B.y // CELL).astype(int)
Gd = B.groupby(["gx", "gy"]).agg(n=("osm", "size"), tagged=("reign", lambda r: int((r != "untagged").sum())), VR=("reign", lambda r: int((r == "VR").sum())),
                                 dated=("dated", "sum")).reset_index()
Gd["share"] = Gd.tagged / Gd.n
inv = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
corners = []
for r in Gd.itertuples():
    xs = [r.gx * CELL, (r.gx + 1) * CELL]; ys = [r.gy * CELL, (r.gy + 1) * CELL]
    lo, la = inv.transform([xs[0], xs[1], xs[1], xs[0]], [ys[0], ys[0], ys[1], ys[1]])
    corners.append([[round(a, 4), round(b, 4)] for a, b in zip(la, lo)])
Gd["corners"] = corners
Gd.drop(columns="corners").to_csv(os.path.join(ROOT, "data", "coverage_grid.csv"), index=False)
g10 = Gd[Gd.n >= 10]
R["grid"] = dict(cell_km=CELL // 1000, cells=len(Gd), cells10=len(g10), ge90=int((g10.share >= .9).sum()), lt50=int((g10.share < .5).sum()),
                 lt25=int((g10.share < .25).sum()), median=float(g10.share.median()))

# ---------- the nearest Victorian box to every town and village ----------
O = pd.read_csv(OSN, sep="\t", dtype=str, quoting=3)
O = O[(O.type == "populatedPlace") & O.local_type.isin(["City", "Town", "Village", "Suburban Area", "Hamlet"])].copy()
for c in ("lat", "lon", "x", "y"): O[c] = O[c].astype(float)
O["area"] = O.county.fillna("").where(O.county.notna() & (O.county != ""), O.district.fillna(""))
O["area"] = O.area.str.split(" - ").str[-1].str.replace(r"^the ", "", regex=True)  # Welsh areas: English name
REIGN_ORDER = ["VR", "EVIIR", "GR", "EVIIIR", "GVIR", "EIIR", "SC", "CIIIR"]
trees = {c: cKDTree(B.loc[B.reign == c, ["x", "y"]].values) for c in REIGN_ORDER}
allt = cKDTree(B[["x", "y"]].values)
O["vr_km"] = trees["VR"].query(O[["x", "y"]].values)[0] / 1000
O["any_km"] = allt.query(O[["x", "y"]].values)[0] / 1000
TW = O[O.local_type.isin(["City", "Town"])]
VI = O[O.local_type == "Village"]
R["nearest"] = dict(towns=len(TW), towns_vr1=int((TW.vr_km <= 1).sum()), towns_vr1_share=float((TW.vr_km <= 1).mean()),
                    towns_vr_median=float(TW.vr_km.median()), villages=len(VI), villages_vr2=int((VI.vr_km <= 2).sum()),
                    villages_vr2_share=float((VI.vr_km <= 2).mean()), villages_vr_median=float(VI.vr_km.median()),
                    villages_vr10=float((VI.vr_km > 10).mean()))
# the oldest reign within 1 km of each town centre
def oldest_within(xy, km):
    for c in REIGN_ORDER:
        if c == "SC": continue
        if len(trees[c].query_ball_point(xy, km * 1000)) > 0: return c
    return ""
TW = TW.copy(); TW["oldest1"] = [oldest_within(p, 1.0) for p in TW[["x", "y"]].values]
R["nearest"]["towns_oldest1"] = {c: int((TW.oldest1 == c).sum()) for c in REIGN_ORDER + [""]}
far = TW[TW.country != "Northern Ireland"].sort_values("vr_km", ascending=False).head(10)
R["nearest"]["towns_far"] = [dict(name=r.name1, area=r.area, km=float(r.vr_km)) for r in far.itertuples()]
# worked examples (named in the text): the oldest boxes near a few places that Wikipedia's "Pillar box" article mentions
EX = [("Framlingham", "Suffolk"), ("Golspie", "Highland"), ("Buxton", "Derbyshire"), ("Cambourne", "Cambridgeshire")]
R["examples"] = {}
for nm, ar in EX:
    o = O[(O.name1 == nm) & (O.area == ar)].iloc[0]
    e = dict(name=nm, area=ar)
    for c in REIGN_ORDER:
        if c == "SC" and ar != "Highland": continue
        dk, ik = trees[c].query([o.x, o.y])
        e[c] = dict(km=float(dk / 1000))
    d1 = np.hypot(B.x - o.x, B.y - o.y) / 1000
    near = B[d1 <= 1.0]
    e["within1"] = {c: int((near.reign == c).sum()) for c in REIGN_ORDER}
    e["designs1"] = {d: int(v) for d, v in near[near.reign == "VR"].design.fillna("not tagged").value_counts().items()}
    R["examples"][nm] = e
# demo places for the page (checked in words): Barrow near Clitheroe is a village in Lancashire
# ---------- towns: the age of the street furniture ----------
T = B[B.bua != ""].groupby("bua").agg(n=("osm", "size"), tagged=("reign", lambda r: int((r != "untagged").sum())), dated=("dated", "sum"),
                                       **{c: ("reign", (lambda c: (lambda r: int((r == c).sum())))(c)) for c in DATED}).reset_index()
T = T.merge(BU[["BUA22CD", "BUA22NM", "pop2021", "LAT", "LONG"]], left_on="bua", right_on="BUA22CD", how="left")
T["tagged_share"] = T.tagged / T.n
T["pre1910_share"] = (T.VR + T.EVIIR) / T.dated.clip(lower=1)
T["pre1936_share"] = (T.VR + T.EVIIR + T.GR + T.EVIIIR) / T.dated.clip(lower=1)
T["vr_share"] = T.VR / T.dated.clip(lower=1)
T["nation"] = np.where(T.bua.str.startswith("S"), "Scotland", np.where(T.bua.str.startswith("W"), "Wales", "England"))
T = T.sort_values("dated", ascending=False)
T[["bua", "BUA22NM", "nation", "pop2021", "LAT", "LONG", "n", "tagged", "dated"] + DATED + ["tagged_share", "vr_share", "pre1910_share", "pre1936_share"]].round(4).to_csv(
    os.path.join(ROOT, "data", "towns.csv"), index=False)
MIN_D, MIN_T = 50, 0.6
TT = T[(T.dated >= MIN_D) & (T.tagged_share >= MIN_T)].copy()
R["towns"] = dict(min_dated=MIN_D, min_tagged=MIN_T, n=len(TT), boxes_in_bua=int((B.bua != "").sum()),
                  median_pre1910=float(TT.pre1910_share.median()), median_pre1936=float(TT.pre1936_share.median()),
                  zero_vr=int((TT.VR == 0).sum()))
def tname(s):
    m = re.match(r"^(.*?) \((.*?)\)$", s)
    if m and (m.group(2).replace(".", "") == m.group(1).replace(".", "")): return m.group(1)
    return s.replace("City and County of the City of London", "City of London")
fmt_t = lambda r: dict(name=tname(r.BUA22NM), nation=r.nation, pop=None if pd.isna(r.pop2021) else int(r.pop2021), dated=int(r.dated),
                       VR=int(r.VR), EVIIR=int(r.EVIIR), pre1910=float(r.pre1910_share), pre1936=float(r.pre1936_share), lat=float(r.LAT), lon=float(r.LONG))
R["towns"]["oldest"] = [fmt_t(r) for r in TT.sort_values(["pre1910_share", "dated"], ascending=[False, False]).head(15).itertuples()]
R["towns"]["youngest"] = [fmt_t(r) for r in TT.sort_values(["pre1936_share", "dated"], ascending=[True, False]).head(15).itertuples()]
TE = TT[TT.pop2021.notna()]
rs = stats.spearmanr(np.log(TE.pop2021), TE.pre1910_share)
R["towns"]["rho_size"] = float(rs.statistic); R["towns"]["p_size"] = float(rs.pvalue); R["towns"]["n_size"] = len(TE)
# size bands
bands = [(0, 50000, "under 50,000"), (50000, 100000, "50,000 to 99,999"), (100000, 250000, "100,000 to 249,999"), (250000, 1e9, "250,000 or more")]
R["towns"]["by_size"] = []
for lo, hi, lab in bands:
    s = TE[(TE.pop2021 >= lo) & (TE.pop2021 < hi)]
    R["towns"]["by_size"].append(dict(band=lab, n=len(s), median_pre1910=float(s.pre1910_share.median()), median_pre1936=float(s.pre1936_share.median())))
# London boroughs vs the rest (BUA22 splits Greater London by borough; these BUA codes are E63004xxx/E63005xxx with borough names)
# validation: does the share of old boxes track how much of a town already existed in 1911?
S = pd.read_csv(SEASIDE)
S = S[S.pop1911.notna() & S.group.isin(["resort", "inland"])].copy()
norm = lambda s: re.sub(r"[^a-z ]", "", re.sub(r"\(.*?\)", "", str(s).lower())).replace("-", " ").strip()
TT["key"] = TT.BUA22NM.map(norm)
tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
S["x"], S["y"] = tr.transform(S.lon.values, S.lat.values)
TT["x"], TT["y"] = tr.transform(TT.LONG.values, TT.LAT.values)
V = []
for r in S.itertuples():
    c = TT[(TT.key == norm(r.place)) | (TT.key == norm(r.place).replace("on sea", "").strip())]
    if not len(c): continue
    dkm = np.hypot(c.x - r.x, c.y - r.y) / 1000
    c = c[dkm < 6]
    if not len(c) or pd.isna(c.iloc[0].pop2021): continue
    b = c.iloc[0]
    V.append(dict(place=r.place, group=r.group, pop1911=int(r.pop1911), bua=b.BUA22NM, pop2021=int(b.pop2021), ratio=r.pop1911 / b.pop2021,
                  dated=int(b.dated), pre1910=float(b.pre1910_share), pre1936=float(b.pre1936_share), vob=r.url))
V = pd.DataFrame(V)
V.to_csv(os.path.join(ROOT, "data", "towns_1911_check.csv"), index=False)
rv = stats.spearmanr(V.ratio, V.pre1910); rv2 = stats.spearmanr(V.ratio, V.pre1936)
R["check1911"] = dict(n=len(V), rho=float(rv.statistic), p=float(rv.pvalue), rho36=float(rv2.statistic), p36=float(rv2.pvalue))
V["half"] = V.ratio >= V.ratio.median()
R["check1911"]["hi_ratio_median_pre1910"] = float(V[V.half].pre1910.median())
R["check1911"]["lo_ratio_median_pre1910"] = float(V[~V.half].pre1910.median())
R["check1911"]["ratio_median"] = float(V.ratio.median())
R["check1911"]["rows"] = V.sort_values("ratio", ascending=False)[["place", "pop1911", "pop2021", "ratio", "dated", "pre1910"]].to_dict("records")

# ---------- Wikidata cross-check ----------
Bw = json.load(gzip.open(BUNDLE))["results"]["wd_postboxes"]["tsv"]
W = pd.read_csv(io.StringIO(Bw), sep="\t", dtype=str); W.columns = [c.lstrip("?") for c in W.columns]
W["qid"] = W.s.str.extract(r"(Q\d+)")
W["label"] = W.label.fillna("").str.replace(r'^"|"@en$', "", regex=True)
W["cls"] = W.clsl.str.replace(r'^"|"@en$', "", regex=True)
W = W.sort_values("qid").groupby("qid").agg(label=("label", "first"), coord=("coord", "first"), cls=("cls", lambda s: ";".join(sorted(set(s)))),
                                           herit=("herit", lambda s: s.notna().any())).reset_index()
m = W.coord.fillna("").str.extract(r"POINT\(([-\d.]+) ([-\d.]+)\)").astype(float)
W["lon"], W["lat"] = m[0], m[1]
Wc = W[W.lat.notna()].copy()
Wc["x"], Wc["y"] = tr.transform(Wc.lon.values, Wc.lat.values)
dd, ii = allt.query(Wc[["x", "y"]].values)
Wc["osm_m"] = dd; Wc["osm_reign"] = B.reign.values[ii]; Wc["osm_penfold"] = B.penfold.values[ii]; Wc["osm"] = B.osm.values[ii]
mt = Wc[Wc.osm_m <= 50]
pfw = Wc[Wc.cls.str.contains("Penfold")]
pfm = pfw[pfw.osm_m <= 50]
R["wikidata"] = dict(items=len(W), with_coord=len(Wc), heritage=int(W.herit.sum()), matched50=len(mt),
                     matched_dated=int(mt.osm_reign.isin(DATED).sum()), matched_vr=int((mt.osm_reign == "VR").sum()),
                     penfold_items=len(pfw), penfold_matched=len(pfm), penfold_matched_tagged=int((pfm.osm_penfold != "").sum()),
                     penfold_matched_vr=int((pfm.osm_reign == "VR").sum()), penfold_matched_sc=int((pfm.osm_reign == "SC").sum()))
Wc[["qid", "label", "cls", "lat", "lon", "osm", "osm_m", "osm_reign", "osm_penfold"]].round({"osm_m": 1}).to_csv(os.path.join(ROOT, "data", "wikidata_check.csv"), index=False)
R["listed"] = dict(osm_listed=int(B.listed.notna().sum()))
R["ciiir"] = dict(n=RD["CIIIR"]["n"], first_date="12 July 2024", first_place="Great Cambourne, Cambridgeshire")

# ---------- page data ----------
RC = {c: i for i, c in enumerate(["VR", "EVIIR", "GR", "EVIIIR", "GVIR", "EIIR", "SC", "CIIIR", "none", "unclear", "untagged"])}
TC = {"pillar": 0, "wall": 1, "lamp": 2, "other": 3, "": 4}
DS = {}
def osmnum(o):
    k, v = o.split("/"); return int(v) if k == "node" else (-int(v) if k == "way" else 0)
dz = [];
for r in B.itertuples():
    des = r.design if isinstance(r.design, str) else ""
    if des not in DS: DS[des] = len(DS)
    dz.append([round(r.lat, 5), round(r.lon, 5), RC[r.reign], TC[r.btype], DS[des], osmnum(r.osm)])
json.dump(dict(reigns=list(RC), types=list(TC), designs=list(DS), rows=dz), open(os.path.join(ROOT, "data", "boxes_page.json"), "w"), separators=(",", ":"))
P = O[O.local_type.isin(["City", "Town", "Village", "Suburban Area"])].copy()
P = P.sort_values(["name1", "local_type"])
pl = [[r.name1, r.area, round(r.lat, 4), round(r.lon, 4), {"City": 0, "Town": 1, "Suburban Area": 2, "Village": 3}[r.local_type]] for r in P.itertuples()]
json.dump(dict(rows=pl), open(os.path.join(ROOT, "data", "places_search.json"), "w"), separators=(",", ":"), ensure_ascii=False)
R["page"] = dict(places=len(pl))

# small page-only data
R["grid_cells"] = [[r.gx, r.gy, int(r.n), int(r.tagged), int(r.VR), r.corners] for r in Gd.itertuples()]
R["area_rows"] = [dict(area=r.area, nation=r.nation, n=int(r.n), tagged=float(r.tagged_share), dated=int(r.dated), VR=int(r.VR), EVIIR=int(r.EVIIR), GR=int(r.GR),
                       EVIIIR=int(r.EVIIIR), GVIR=int(r.GVIR), EIIR=int(r.EIIR), SC=int(r.SC), CIIIR=int(r.CIIIR)) for r in A.sort_values("n", ascending=False).itertuples() if r.area]
R["town_rows"] = [fmt_t(r) | dict(tagged=float(r.tagged_share)) for r in TT.sort_values("dated", ascending=False).itertuples()]


def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating, float)): return None if np.isnan(o) else round(float(o), 6)
    return o


json.dump(clean(R), open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
for k in ("meta", "tag", "old", "scotland", "edward8", "victoria", "penfold", "bias", "grid", "nearest", "towns", "check1911", "wikidata"):
    v = {a: b for a, b in R[k].items() if not isinstance(b, list)}
    print(k, json.dumps(clean(v)))
for r in rows: print(r["code"], r["n"], round(r["share"], 4), round(r["per_year"], 1), r["pillar"], r["wall"], r["lamp"])
print(json.dumps(clean(R["examples"])))
print(json.dumps(clean(R["towns"]["oldest"][:8])))
print(json.dumps(clean(R["towns"]["youngest"][:8])))
print(json.dumps(clean(R["areas"]["vr_top"][:6])), json.dumps(clean(R["areas"]["tag_bottom"])))
