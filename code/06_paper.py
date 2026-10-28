"""Step 6. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Postbox_Kings.tex and compile it with xelatex (figures from step 5).
Run: python3 code/06_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Postbox_Kings"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}".replace("-", "$-$")
    if f == "f3": return f"{v:.3f}"
    if f == "p": return "$<$ 0.001" if v < 0.001 else f"= {v:.3f}"
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


rows = "".join(f"{tex(r['short'])} & {tex(r['span'])} & {r['n']:,} & {r['share'] * 100:.1f} & {r['years']:.1f} & {r['per_year']:.0f} & {r['pillar']:,} & {r['wall']:,} & {r['lamp']:,}\\\\\n" for r in R["reigns"])
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Mapped UK post boxes by royal cypher. Share: percentage of the "
      f"{R['tag']['dated']:,} boxes with a known reign. Years: years in which boxes with the cypher could be made (see Methods).}}\\label{{tab:reigns}}"
      "\\begin{tabular}{llrrrrrrr}\\toprule Cypher & Reign & Boxes & Share & Years & Per year & Pillar & Wall & Lamp\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
fr = lambda r: f"{tex(r['name'])} & {r['pop']:,} & {r['dated']} & {r['pre1910'] * 100:.0f} & {r['pre1936'] * 100:.0f}\\\\\n" if r["pop"] else f"{tex(r['name'])} & n/a & {r['dated']} & {r['pre1910'] * 100:.0f} & {r['pre1936'] * 100:.0f}\\\\\n"
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{Towns and districts (2022 built-up areas) with the highest share of boxes from before 1910 and the lowest share from before 1936. "
      f"Towns with at least {R['towns']['min_dated']} boxes of known reign and {R['towns']['min_tagged'] * 100:.0f}\\% of boxes tagged. Population: Census 2021 (not available here for Scotland).}}\\label{{tab:towns}}"
      "\\begin{tabular}{lrrrr}\\toprule Town or district & Population & Dated boxes & \\% before 1910 & \\% before 1936\\\\\\midrule\n"
      "\\multicolumn{5}{l}{\\emph{Oldest}}\\\\\n" + "".join(fr(r) for r in R["towns"]["oldest"][:10]) +
      "\\midrule\\multicolumn{5}{l}{\\emph{Youngest}}\\\\\n" + "".join(fr(r) for r in R["towns"]["youngest"][:10]) + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_REIGNS}}", TR).replace("{{TABLE_TOWNS}}", TT)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper written", r.returncode)
