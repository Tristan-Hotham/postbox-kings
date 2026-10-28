"""Step 7. Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader (numbers inside them are filled).
Run: python3 code/07_release.py
"""
import importlib.util, json, os, re, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "03_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--"): assert bad not in vis, bad
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
meta = dict(
    title="What's the king on your postbox?",
    slug="postbox-kings",
    excerpt=(f"OpenStreetMap's volunteers have read the royal cypher on {R['tag']['dated']:,} UK post boxes. {R['victoria']['n']:,} still carry Victoria's VR, "
             f"{R['edward8']['n']} the cypher of Edward VIII, and the mix on a town's streets says something about when it was built."),
    seo_description=f"{R['meta']['n']:,} UK post boxes by royal cypher: {R['victoria']['n']:,} Victorian, {R['edward8']['n']} Edward VIII, and the oldest postbox near you.",
    tags=["post boxes", "pillar boxes", "royal cypher", "OpenStreetMap", "street furniture", "Royal Mail", "maps", "data"],
    header_alt=(f"Title card reading 'What's the king on your postbox?' in dark ink and pillar-box red on cream, beside a map of the United Kingdom "
                f"dotted with Victorian boxes in dark blue, Edward VII boxes in purple and Edward VIII boxes as gold circles. Text: {R['meta']['n']:,} UK post boxes "
                f"in OpenStreetMap; {R['victoria']['n']:,} still carry Queen Victoria's VR; {R['edward8']['n']} carry the cypher of Edward VIII, who reigned for 325 days."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_Postbox_Kings"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$\\rho$", "rho").replace("$<$", "<")
assert "\\" not in ab and "$" not in ab, ab
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="What's the King on Your Postbox? Royal Cyphers on the Post Boxes of the United Kingdom in OpenStreetMap",
    description_html=f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/postbox-kings/. Data and code: https://github.com/Tristan-Hotham/postbox-kings. Blog post: to follow.</p><p>The data files derived from OpenStreetMap are released under the Open Database Licence (ODbL 1.0); the paper and other material under CC BY 4.0. Contains OpenStreetMap data © OpenStreetMap contributors; contains OS data © Crown copyright and database right 2026.</p>",
    keywords=["post boxes", "pillar boxes", "royal cypher", "street furniture", "OpenStreetMap", "volunteered geographic information",
              "Royal Mail", "Pillar Box War", "urban history", "United Kingdom"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/postbox-kings", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/postbox-kings/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://www.openstreetmap.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://geoportal.statistics.gov.uk", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.nomisweb.co.uk", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://en.wikipedia.org/wiki/Pillar_box", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://en.wikipedia.org/wiki/Pillar_Box_War", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://portal.historicenvironment.scot/designation/LB52465", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://doi.org/10.5281/zenodo.23727127", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["postboxes.csv", "reigns.csv", "areas.csv", "towns.csv", "edward_viii.csv", "towns_1911_check.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "postbox-kings_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"postbox-kings/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"postbox-kings/{f}")
words = len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split())
print("release files written; post words:", words)
