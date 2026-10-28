"""Step 1. Read every UK post box in OpenStreetMap, normalise its royal cypher and place it.

Input : /home/claude/hist/_data12/wd_osm_bundle12.json.gz, key osm_postboxes (OpenStreetMap, ODbL,
        amenity=post_box inside the UK relation 62149, via QLever, retrieved 28 October 2026)
        /home/claude/hist/osnames_gb.tsv (OS Open Names, OGL v3) for the nearest named place, county and nation
        /home/claude/hist/_data8/ons_geo.json (ONS BUA22 centroids and areas, MSOA 2021 centroids and lookups, OGL v3)
        /home/claude/hist/_data8/lsoa21_bua22_lookup.json and census/census2021-ts001-lsoa.csv (Census 2021 population)
Output: work/boxes.pkl, work/bua.pkl, data/postboxes.csv

Royal cypher (OSM tag royal_cypher) is mapped to a reign:
  VR Victoria (boxes from 1853 to 1901), EVIIR Edward VII (1901 to 1910), GR George V (1910 to 1936; one box tagged GVR),
  EVIIIR Edward VIII (1936), GVIR George VI (1936 to 1952), EIIR Elizabeth II (1952 to 2022), CIIIR Charles III (2022 on),
  scottish_crown (the Crown of Scotland used on Scottish boxes since the Pillar Box War of 1952 to 1953),
  no (a box with no cypher: Victorian "anonymous" boxes of 1879 to 1887, private and some modern boxes),
  unclear (yes, obscured, crown, ER, or two values) and untagged (no royal_cypher tag at all).
Run: python3 code/01_prepare.py
"""
import gzip, io, json, os, re
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
BUNDLE = "/home/claude/hist/_data12/wd_osm_bundle12.json.gz"
OSN = "/home/claude/hist/osnames_gb.tsv"
D8 = "/home/claude/hist/_data8"
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)

B = json.load(gzip.open(BUNDLE))
RET = B["retrieved"][:10]
df = pd.read_csv(io.StringIO(B["results"]["osm_postboxes"]["tsv"]), sep="\t", dtype=str, quoting=3)
df.columns = [c.lstrip("?") for c in df.columns]
for c in df.columns:
    df[c] = df[c].str.strip().str.strip('"')
df["osm"] = df.osm.str.strip("<>").str.replace("https://www.openstreetmap.org/", "", regex=False)
raw_rows = len(df)


def pt(w):
    """Point for a WKT geometry: the point itself, or the mean vertex of a polygon or line."""
    nums = re.findall(r"(-?\d+\.?\d*) (-?\d+\.?\d*)", w or "")
    if not nums: return (np.nan, np.nan)
    a = np.array(nums, dtype=float)
    return (a[:, 1].mean(), a[:, 0].mean())


# one row per OSM object: rows repeat when a tag has several values; keep distinct values joined by ";"
dup = df.osm.duplicated(keep=False)
one = df[~dup].fillna("")
many = df[dup].groupby("osm").agg(lambda s: ";".join(dict.fromkeys(v for v in s.dropna() if v != ""))).reset_index()
many["wkt"] = many.wkt.str.split(";").str[0]
agg = pd.concat([one, many], ignore_index=True).replace("", np.nan)
ll = agg.wkt.map(pt)
agg["lat"] = [a for a, b in ll]; agg["lon"] = [b for a, b in ll]
agg = agg.drop(columns="wkt")
agg["kind"] = agg.osm.str.split("/").str[0]

REIGN = {"VR": "VR", "EVIIR": "EVIIR", "GR": "GR", "GVR": "GR", "EVIIIR": "EVIIIR", "GVIR": "GVIR", "EIIR": "EIIR",
         "CIIIR": "CIIIR", "scottish_crown": "SC", "no": "none"}


def reign(c):
    if not isinstance(c, str) or not c: return "untagged"
    c = c.strip()
    if ";" in c: return "unclear"
    return REIGN.get(c, "unclear")


agg["reign"] = agg.cypher.map(reign)


def btype(t):
    t = (t if isinstance(t, str) else "").split(";")[0]
    return t if t in ("pillar", "wall", "lamp") else ("other" if t else "")


agg["btype"] = agg.ptype.map(btype)
d = agg.design.fillna("")
agg["penfold"] = np.where(d.str.contains("reproduction_penfold"), "replica", np.where(d.str.contains("penfold"), "original", ""))

# ---- nation, county and nearest named place (OS Open Names) ----
tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
agg["x"], agg["y"] = tr.transform(agg.lon.values, agg.lat.values)
O = pd.read_csv(OSN, sep="\t", dtype=str, quoting=3)
O = O[O.type == "populatedPlace"].copy()
for c in ("lat", "lon", "x", "y"): O[c] = O[c].astype(float)
O["area"] = O.county.fillna("").where(O.county.notna() & (O.county != ""), O.district.fillna(""))
O["area"] = O.area.str.split(" - ").str[-1].str.replace(r"^the ", "", regex=True)  # Welsh areas: English name
O["rank"] = O.local_type.map({"City": 0, "Town": 1, "Suburban Area": 2, "Village": 3, "Hamlet": 4, "Other Settlement": 5})
t = cKDTree(O[["x", "y"]].values)
dist, idx = t.query(agg[["x", "y"]].values)
agg["os_km"] = dist / 1000
agg["near_place"] = O.name1.values[idx]; agg["near_type"] = O.local_type.values[idx]
agg["area"] = O.area.values[idx]; agg["nation"] = O.country.values[idx]
# the nearest town or city name (for "town" labels in the search and tables)
TC = O[O["rank"] <= 1]
tt = cKDTree(TC[["x", "y"]].values); dt, it = tt.query(agg[["x", "y"]].values)
agg["near_town"] = TC.name1.values[it]; agg["near_town_km"] = dt / 1000
ni = (agg.lon < -5.42) & agg.lat.between(54.0, 55.32) & (agg.os_km > 4)
ni |= (agg.lon < -5.9) & agg.lat.between(54.0, 55.32)
ni &= ~((agg.lon > -5.2))
agg.loc[ni, ["nation", "area"]] = ["Northern Ireland", "Northern Ireland"]
agg.loc[ni, ["near_place", "near_type", "near_town"]] = ""
far = ~ni & (agg.os_km > 20)
print("far from any OS name (kept, nation from nearest):", int(far.sum()))

# ---- built-up area 2022 (Great Britain) by centroid and equivalent radius ----
# ONS publishes BUA22 centroids and areas but I have no polygons here, so a box is put in the built-up area whose centroid is
# nearest in units of that area's equivalent radius (the radius of a circle of the same area), if that is 1.25 or less.
# Ragged or long towns lose some outlying boxes and a few boxes are put in a neighbour; the town measures are shares, not counts.
G = json.load(open(os.path.join(D8, "ons_geo.json")))
BU = pd.DataFrame(G["bua22_gb"])[["BUA22CD", "BUA22NM", "LAT", "LONG", "BNG_E", "BNG_N", "Shape__Area"]]
BU["r"] = np.sqrt(BU.Shape__Area / np.pi)
lk = pd.DataFrame(json.load(open(os.path.join(D8, "lsoa21_bua22_lookup.json"))))
pop = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-lsoa.csv"))
pop = pop.rename(columns={"geography code": "LSOA21CD", "Residence type: Total; measures: Value": "pop"})[["LSOA21CD", "pop"]]
lkc = [c for c in lk.columns if c.upper().startswith("LSOA")][0]
lk = lk.rename(columns={lkc: "LSOA21CD"}).merge(pop, on="LSOA21CD", how="left")
bpop = lk.groupby("BUA22CD")["pop"].sum()
BU["pop2021"] = BU.BUA22CD.map(bpop)
bt = cKDTree(BU[["BNG_E", "BNG_N"]].values)
cand = bt.query(agg[["x", "y"]].values, k=8, distance_upper_bound=40000)
best = np.full(len(agg), -1); bestv = np.full(len(agg), np.inf)
for j in range(8):
    dd = cand[0][:, j]; ii = cand[1][:, j]
    ok = np.isfinite(dd)
    rr = np.where(ok, BU.r.values[np.minimum(ii, len(BU) - 1)], 1.0)
    v = np.where(ok, dd / (rr + 150.0), np.inf)  # distance in units of the area's equivalent radius (plus 150 m)
    upd = v < bestv
    best[upd] = ii[upd]; bestv[upd] = v[upd]
inb = bestv <= 1.25
agg["bua"] = np.where(inb, BU.BUA22CD.values[np.maximum(best, 0)], "")
agg["bua_name"] = np.where(inb, BU.BUA22NM.values[np.maximum(best, 0)], "")
agg.loc[agg.nation == "Northern Ireland", ["bua", "bua_name"]] = ""

agg.to_pickle(os.path.join(ROOT, "work", "boxes.pkl"))
BU.to_pickle(os.path.join(ROOT, "work", "bua.pkl"))
json.dump({"retrieved": RET, "raw_rows": raw_rows}, open(os.path.join(ROOT, "work", "meta.json"), "w"))

out = agg[["osm", "lat", "lon", "cypher", "reign", "btype", "design", "penfold", "mounting", "ref", "listed",
           "nation", "area", "near_place", "bua_name"]].copy()
out["lat"] = out.lat.round(5); out["lon"] = out.lon.round(5)
out = out.rename(columns={"cypher": "royal_cypher_tag", "btype": "box_type", "design": "post_box_design_tag"})
out["osm"] = out.osm.str.replace("node/", "n", regex=False).str.replace("way/", "w", regex=False)
out.to_csv(os.path.join(ROOT, "data", "postboxes.csv"), index=False)
print(len(agg), "boxes from", raw_rows, "rows")
print(agg.reign.value_counts().to_string())
print(agg.nation.value_counts().to_string())
print("in a BUA:", int(inb.sum()))
