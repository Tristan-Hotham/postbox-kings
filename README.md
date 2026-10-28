# What's the king on your postbox?

Every British post box carries the royal cypher of the monarch who reigned when it was made: VR, EVIIR, GR, EVIIIR, GVIR, EIIR, CIIIR, or the Crown of Scotland. This study counts the surviving boxes of each reign in OpenStreetMap, maps the Victorian and Edward VIII survivors, asks whether the cyphers on a town's boxes say when it was built, and checks how complete the volunteer map is. The page has a "find the oldest postbox near you" search by place, postcode or location.

**Interactive version:** https://tristan-hotham.github.io/postbox-kings/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23729633

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- OpenStreetMap (28 October 2026) holds 90,190 UK post boxes, about 78% of the 115,000 Royal Mail reported in 2002. 61,435 have a cypher of a known reign; 27,168 (30%) have no cypher tag.
- Elizabeth II is on 36,452 boxes (59% of those with a known reign), George V 9,809, George VI 4,718, the Scottish crown 3,963, Victoria 3,614, Edward VII 2,663, Edward VIII 143 and Charles III 73.
- Per year in which boxes could be made, Victoria has 75 survivors a year against 516 for Elizabeth II; Edward VIII's 143 boxes over an eleven-month reign give 160 a year, more than twice Victoria's rate.
- 2,173 of the 3,614 Victorian boxes are wall boxes; 45 VR boxes are tagged as 1980s reproduction Penfolds, leaving 3,569. 82 boxes are tagged as original Penfolds (Wikipedia: about 150 survive).
- The 143 Edward VIII boxes are 84% of the 171 survivors identified by the Letter Box Study Group (as quoted by Historic Environment Scotland); 135 are pillar boxes, which fits the replacement of wall and lamp box doors after the abdication. Greater London has 26, Glasgow 15.
- In Scotland 3,933 boxes carry the Crown of Scotland and only 39 EIIR: 99% crown, the legacy of the Pillar Box War of 1952 and 1953.
- In 131 well-mapped towns, the share of boxes from before 1910 runs from 48% in the City of London to almost none in Glenrothes, Stevenage, Crawley, Milton Keynes and Livingston. For 16 towns with a 1911 census population, the share rises with the share of today's population already present in 1911 (Spearman's rho 0.63).
- Tagging ranges from 30% of boxes (County Durham) to 100% (Wirral), but well-tagged areas are not older: Victorian boxes are 5.1% of dated boxes where at least 90% are tagged, against 5.9% overall.
- 376 of 1,426 towns and cities (26%) have a mapped Victorian box within a kilometre of their OS Open Names point.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page: "find yours" search, a map of every box by reign with a coverage layer, charts and tables. Results are embedded; boxes and place names are loaded from `data/`. |
| `header.png` | Social card (1200 by 630). |
| `data/postboxes.csv` | One row per mapped box (90,190): OSM id (n = node, w = way), latitude, longitude, the royal_cypher tag as mapped, reign, box type, design tag, Penfold flag, mounting, Royal Mail ref, listed status, nation, county or unitary area, nearest OS Open Names place, 2022 built-up area. |
| `data/reigns.csv` | Boxes by reign, share, years of production, boxes per year, by kind and nation. |
| `data/areas.csv` | Counts by reign and tagging share for each county, unitary area or metropolitan district. |
| `data/towns.csv` | Counts by reign for every 2022 built-up area with at least one box, Census 2021 population, tagging share and shares before 1910 and 1936. |
| `data/towns_1911_check.csv` | The 16 towns matched to a 1911 census population (A Vision of Britain through Time, with links). |
| `data/edward_viii.csv` | The 143 boxes tagged EVIIIR. |
| `data/coverage_grid.csv` | 20 km British National Grid squares: boxes, tagged boxes, Victorian boxes. |
| `data/wikidata_check.csv` | Wikidata post boxes and the nearest OpenStreetMap box. |
| `data/boxes_page.json`, `data/places_search.json` | Compact box list and OS Open Names place list for the page. |
| `data/coast_ne10m.json` | Natural Earth 1:10m land (public domain) for the header and figures. |
| `data/results.json` | Every number used anywhere. |
| `code/01_prepare.py` | Reads the OpenStreetMap extract, merges repeated rows, maps cyphers to reigns, adds nation, area, nearest place and built-up area. |
| `code/02_analyse.py` | All statistics; writes the data tables, `results.json` and the page data. |
| `code/03_build_site.py` | Fills `code/page_template.html` to make `index.html` and checks facts stated in words. |
| `code/04_header.py` | Renders `header.png` with Playwright. |
| `code/05_figures.py` | Static figures for the paper and blog. |
| `code/06_paper.py` | Builds the paper PDF from `code/paper_template.tex` with xelatex. |
| `code/07_release.py` | Blog post, blog and Zenodo metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Boxes.** Every OpenStreetMap object tagged `amenity=post_box` inside the UK (relation 62149), via the QLever OpenStreetMap endpoint: 91,456 rows merged to 90,190 boxes.
- **Reigns.** `royal_cypher` VR, EVIIR, GR (one GVR), EVIIIR, GVIR, EIIR, CIIIR and `scottish_crown`. "no" = no cypher (including Victorian anonymous boxes of 1879 to 1887); "yes", "obscured", "crown", "ER" or two values = unclear; no tag = untagged.
- **Years of production.** Victoria from 1853 (the first mainland box) to 22 January 1901; Edward VII to 6 May 1910; George V to 20 January 1936; Edward VIII to 11 December 1936; George VI to 6 February 1952; Elizabeth II to 8 September 2022; the Scottish crown from 1953; Charles III from 12 July 2024 (the first CIIIR box) to the data date.
- **Places.** County or unitary area and nation from the nearest OS Open Names populated place; Northern Ireland by position. Towns: the 2022 built-up area whose centroid is nearest in units of its equivalent radius (within 1.25 radii); no outlines were used. Towns analysed: at least 50 dated boxes and 60% of boxes tagged. Census 2021 populations summed from LSOAs.
- **Checks.** Reign mix in areas with 90% or more tagged; rank correlation between tagging and old boxes; Wikidata post boxes matched within 50 m; 1911 populations for 16 towns from my seaside railways study.

## Known limits

- These are mapped and tagged boxes, roughly half of all boxes, and tagging varies a lot by area. Royal Mail's 115,000 dates from 2002.
- A cypher dates the casting, not the installation. Boxes are moved and reused, doors are swapped (most Edward VIII wall and lamp boxes got George VI doors), replicas copy old cyphers, and some tags are wrong (two "original" Penfolds are in Scotland, where Wikipedia says there are none).
- Town assignment uses centroids and areas, not outlines. The 1911 check uses only 16 towns, mostly resorts, with different boundaries.
- The Edward VIII and Penfold totals I compare with come from secondary sources (Historic Environment Scotland's listing text and Wikipedia).

## How to rerun

Inputs are read from the paths at the top of each script: the OpenStreetMap and Wikidata extract `wd_osm_bundle12.json.gz` (QLever, 28 October 2026), OS Open Names (`osnames_gb.tsv`, compact), the ONS geography and Census 2021 files, and `data/places.csv` from https://github.com/Tristan-Hotham/seaside-railways.

```
python3 code/01_prepare.py
python3 code/02_analyse.py
python3 code/03_build_site.py
FONT_DIR=path/to/fonts python3 code/04_header.py
FONT_DIR=path/to/fonts python3 code/05_figures.py
python3 code/06_paper.py
python3 code/07_release.py
```

Needs Python 3 with pandas, numpy, scipy, pyproj, matplotlib and playwright, and xelatex with TeX Gyre Pagella and Inter for the paper.

## Sources and licences

- Post boxes: © OpenStreetMap contributors, Open Database Licence 1.0 (https://www.openstreetmap.org/copyright), via QLever (https://qlever.cs.uni-freiburg.de).
- Places: OS Open Names, contains OS data © Crown copyright and database right 2026 (Open Government Licence v3.0).
- Built-up areas 2022, LSOA lookup and Census 2021 TS001: Office for National Statistics (Open Government Licence v3.0).
- Wikidata post boxes: CC0.
- History: English Wikipedia, "Pillar box", "Post box", "Royal cypher" and "Pillar Box War" (CC BY-SA 4.0). Edward VIII figures: Historic Environment Scotland, listing LB52465 (https://portal.historicenvironment.scot/designation/LB52465).
- 1911 populations: A Vision of Britain through Time, University of Portsmouth, via my study https://doi.org/10.5281/zenodo.23727127.
- Postcode lookups on the page: postcodes.io (ONS and OS open data). Coastline: Natural Earth (public domain). Base map tiles © Esri. Map library: Leaflet.

The data files derived from OpenStreetMap are released under the ODbL 1.0 (see `LICENSE` for the list). Text and figures: CC BY 4.0. Code: MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) What's the King on Your Postbox? Royal Cyphers on the Post Boxes of the United Kingdom in OpenStreetMap. Zenodo. https://doi.org/10.5281/zenodo.23729633

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
