"""Step 3. Build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json, so the page cannot drift from the
analysis. Facts the template states in words are checked against the data below. The results are embedded; the box
list (data/boxes_page.json) and the place list for the search (data/places_search.json) are fetched by the page.
Run: python3 code/03_build_site.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


# facts stated in words in the template
RD = {r["code"]: r for r in R["reigns"]}
assert [r["code"] for r in R["reigns"]] == ["VR", "EVIIR", "GR", "EVIIIR", "GVIR", "EIIR", "SC", "CIIIR"]
assert sorted(RD, key=lambda c: -RD[c]["n"])[:6] == ["EIIR", "GR", "GVIR", "SC", "VR", "EVIIR"]
assert RD["EVIIIR"]["per_year"] >= 2 * RD["VR"]["per_year"]
assert abs(RD["VR"]["years"] - 48) < 0.2
assert R["victoria"]["wall"] > R["victoria"]["n"] / 2 and RD["EIIR"]["lamp"] > R["types"]["lamp"] / 2
assert R["examples"]["Framlingham"]["designs1"] == {"octagonal": 2}
assert [a["area"] for a in R["edward8"]["top_areas"][:2]] == ["Greater London", "Glasgow City"]
assert R["edward8"]["pillar"] > 0.9 * R["edward8"]["n"]
T = {t["name"]: t for t in R["town_rows"]}
for nm in ["Glenrothes", "Stevenage", "Crawley", "Milton Keynes", "Livingston"]:
    assert T[nm]["VR"] + T[nm]["EVIIR"] <= 2, nm
old = [t["name"] for t in R["towns"]["oldest"]]
assert old[:5] == ["City of London", "Hammersmith and Fulham", "Haringey", "Wandsworth", "Camden"]
assert [n for n in old if n in ("Manchester", "Royal Tunbridge Wells", "Bournemouth", "Cheltenham")] == ["Manchester", "Royal Tunbridge Wells", "Bournemouth", "Cheltenham"]
assert all(.35 <= T[n]["pre1910"] < .45 for n in ["Hammersmith and Fulham", "Haringey", "Wandsworth", "Camden"])
young = [t["name"] for t in R["towns"]["youngest"]]
assert all(n in young for n in ["Chichester", "Newbury", "Chelmsford"])
C = {r["place"]: r for r in R["check1911"]["rows"]}
assert all(C[n]["ratio"] < 1 / 7 and C[n]["pre1910"] < .02 for n in ["Aylesbury", "Bognor Regis"])
assert all(C[n]["pre1910"] > .2 for n in ["Bournemouth", "Margate", "Scarborough"])
assert R["areas"]["tag_bottom"][0]["area"] == "County Durham" and R["areas"]["tag_top"][0]["area"] == "Wirral"
assert min(R["nations"], key=lambda e: e["n"])["nation"] == "Northern Ireland" == min(R["nations"], key=lambda e: e["tagged_share"])["nation"]
assert R["bias"]["vr_share"] < R["bias"]["all_vr_share"] and R["bias"]["pre1936_share"] < R["bias"]["all_pre1936_share"]
assert R["nearest"]["towns_far"][0]["name"] == "Stornoway"
assert R["check1911"]["n"] == 16  # "Sixteen towns" in the page and blog text
assert all(T[n]["VR"] + T[n]["EVIIR"] <= 2 for n in ["Havant", "Newbury"])  # paper text
assert R["scotland"]["eiir_types"]["lamp"] > R["scotland"]["eiir"] / 2

if __name__ == "__main__":
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    slim = {k: v for k, v in R.items() if k not in ("area_rows",)}
    html = html.replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in html
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)  # tags and their attributes are not visible text
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
