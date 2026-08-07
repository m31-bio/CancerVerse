#!/usr/bin/env python3
"""Render the coverage table as a standalone reviewable page.

    python scripts/build_coverage_page.py [output.html]

Same data as the README table, laid out so a 7-column x 36-row grid is actually
readable. Generated from registry/models.yaml.
"""

from __future__ import annotations

import html
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "models.yaml"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_table import (  # noqa: E402
    AXES,
    AXIS_LABEL,
    GAP_CAPTION,
    GAP_CELL_LABEL,
)
from model_table import (
    DISEASE_LABEL as _DISEASE_LABEL,
)
from model_table import (
    OPEN_SOURCE_LABEL as SOURCE_LABEL,
)

# the page is HTML, so the ampersand needs escaping
DISEASE_LABEL = {k: v.replace("&", "&amp;") for k, v in _DISEASE_LABEL.items()}
SOURCE_CLASS = {"available": "src-code", "web_only": "src-web", "none": "src-paper"}


def e(x) -> str:
    return html.escape(" ".join(str(x or "").split()))


CSS = """
:root{
  --ink:#16211f; --ink-2:#33413e; --muted:#5f6d6a;
  --paper:#f6f8f7; --card:#ffffff; --rule:#dde4e1; --rule-2:#eef2f0;
  --accent:#0f6e5c; --accent-soft:#e4f0ec;
  --warn:#8a5410; --warn-soft:#f7ecdd;
  --band:#f0f4f2;
}
@media (prefers-color-scheme: dark){
  :root{
    --ink:#e6ece9; --ink-2:#c2ccc8; --muted:#8b9995;
    --paper:#0e1413; --card:#151d1b; --rule:#26302d; --rule-2:#1c2523;
    --accent:#4fbfa4; --accent-soft:#12302a;
    --warn:#d9a05b; --warn-soft:#2e2418;
    --band:#121a18;
  }
}
:root[data-theme="dark"]{
  --ink:#e6ece9; --ink-2:#c2ccc8; --muted:#8b9995;
  --paper:#0e1413; --card:#151d1b; --rule:#26302d; --rule-2:#1c2523;
  --accent:#4fbfa4; --accent-soft:#12302a;
  --warn:#d9a05b; --warn-soft:#2e2418;
  --band:#121a18;
}
:root[data-theme="light"]{
  --ink:#16211f; --ink-2:#33413e; --muted:#5f6d6a;
  --paper:#f6f8f7; --card:#ffffff; --rule:#dde4e1; --rule-2:#eef2f0;
  --accent:#0f6e5c; --accent-soft:#e4f0ec;
  --warn:#8a5410; --warn-soft:#f7ecdd;
  --band:#f0f4f2;
}


*{box-sizing:border-box;}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  font-size:15px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1500px;margin:0 auto;padding:40px 28px 80px;}

header{border-bottom:2px solid var(--ink);padding-bottom:22px;margin-bottom:28px;}
.eyebrow{
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);font-weight:650;margin-bottom:10px;
}
h1{
  font-family:"Iowan Old Style","Charter","Palatino Linotype",Palatino,Georgia,serif;
  font-size:clamp(30px,4vw,44px); line-height:1.08; margin:0 0 10px;
  font-weight:600; letter-spacing:-.01em; text-wrap:balance;
}
.sub{color:var(--muted);max-width:64ch;margin:0;font-size:15.5px;}

.stats{display:flex;flex-wrap:wrap;gap:0;margin:26px 0 0;
  border:1px solid var(--rule);border-radius:3px;overflow:hidden;background:var(--card);}
.stat{flex:1 1 170px;padding:16px 18px;border-right:1px solid var(--rule);}
.stat:last-child{border-right:0;}
.stat b{
  display:block;font-size:27px;font-weight:600;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;color:var(--accent);line-height:1.1;
}
.stat span{display:block;font-size:12.5px;color:var(--muted);margin-top:3px;}

.note{
  margin:26px 0 0;padding:13px 16px;border-left:3px solid var(--warn);
  background:var(--warn-soft);border-radius:0 3px 3px 0;font-size:13.5px;color:var(--ink-2);
}

.scroller{
  margin-top:30px;overflow-x:auto;border:1px solid var(--rule);
  border-radius:3px;background:var(--card);
}
table{border-collapse:collapse;width:100%;min-width:1980px;font-size:13.5px;}
thead th{
  position:sticky;top:0;z-index:2;background:var(--card);
  border-bottom:2px solid var(--ink);
  text-align:left;padding:11px 13px;font-size:11px;letter-spacing:.09em;
  text-transform:uppercase;color:var(--ink);font-weight:650;white-space:nowrap;
}
td{padding:12px 13px;border-bottom:1px solid var(--rule-2);vertical-align:top;}
tr.group-start td{border-top:1px solid var(--ink);}
tr.banded td{background:var(--band);}
/* Merged cells. The disease cell spans all three questions and the question
   cell spans its models, so neither carries an internal horizontal rule — a
   vertical rule marks the boundary instead. */
td.disease,td.axis{border-right:1px solid var(--rule);border-bottom:0;}
td.disease{
  font-family:"Iowan Old Style","Charter",Palatino,Georgia,serif;
  font-size:17px;font-weight:600;white-space:nowrap;width:1%;
  padding-top:14px;letter-spacing:-.005em;
}
td.axis{
  color:var(--ink-2);white-space:nowrap;width:1%;font-size:13px;
  padding-top:13px;
}
td.model{font-weight:600;min-width:150px;}
td.cite{color:var(--muted);font-size:11.5px;min-width:180px;max-width:230px;line-height:1.4;}
td.repo{font-size:12px;min-width:145px;max-width:185px;}
td.repo a,td.cite a{color:var(--accent);text-decoration:none;
  border-bottom:1px solid var(--rule);overflow-wrap:anywhere;font-weight:600;}
td.repo a:hover,td.cite a:hover{border-bottom-color:var(--accent);}
td.arch{min-width:230px;max-width:300px;}
.fam{
  display:inline-block;font-size:11px;letter-spacing:.05em;text-transform:uppercase;
  font-weight:650;color:var(--accent);
}
.archline{margin-top:5px;font-size:12px;color:var(--ink-2);line-height:1.45;}
td.formula{min-width:340px;max-width:480px;}
td.formula pre{
  margin:0;
  font-family:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  font-size:11.5px;line-height:1.62;color:var(--ink);
  white-space:pre;overflow-x:auto;
  padding:9px 11px;background:var(--band);border-radius:3px;
  border-left:2px solid var(--accent);
}
tr.banded td.formula pre{background:var(--card);}
td.year{
  font-size:18px;font-weight:600;color:var(--ink);width:1%;
  font-variant-numeric:tabular-nums;white-space:nowrap;padding-top:13px;
}
td.perf{min-width:195px;max-width:255px;}
.disc{font-size:12px;color:var(--accent);font-weight:600;line-height:1.4;}
.unrec{font-size:11.5px;color:var(--muted);font-style:italic;line-height:1.4;}
.coh{margin-top:5px;font-size:11.5px;color:var(--muted);line-height:1.4;}
td.verified{min-width:230px;max-width:330px;}
code{
  font-family:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  font-size:11.8px;line-height:1.55;color:var(--ink);
  overflow-wrap:anywhere;display:block;
}
.empty td{color:var(--muted);}
.dash{color:var(--rule);font-size:17px;}
.gapnote{font-size:11.5px;color:var(--muted);font-style:italic;}

.chip{
  display:inline-block;padding:2px 8px;border-radius:2px;
  font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;font-weight:650;
  white-space:nowrap;
}
.ok{background:var(--accent-soft);color:var(--accent);}
.src-code{background:var(--accent-soft);color:var(--accent);}
.src-web{background:var(--warn-soft);color:var(--warn);}
.src-paper{background:transparent;color:var(--muted);border:1px solid var(--rule);}
.how{margin-top:6px;font-size:12px;color:var(--ink-2);line-height:1.45;}
.repro{margin-top:9px;padding-top:8px;border-top:1px dashed var(--rule);}
.repro>span{
  font-size:10px;letter-spacing:.09em;text-transform:uppercase;
  font-weight:650;color:var(--accent);
}
.repro ul{margin:5px 0 0;padding-left:15px;}
.repro li{font-size:11.5px;color:var(--muted);margin-bottom:3px;line-height:1.45;}
.repro code{display:inline;font-size:11px;color:var(--ink-2);}
details{margin-top:5px;}
summary{
  cursor:pointer;font-size:11.5px;color:var(--accent);
  list-style:none;font-weight:600;
}
summary::-webkit-details-marker{display:none;}
summary::before{content:"+ ";font-weight:700;}
details[open] summary::before{content:"\\2212 ";}
details p{margin:6px 0 0;font-size:12px;color:var(--muted);line-height:1.5;}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px;}

footer{margin-top:34px;padding-top:20px;border-top:1px solid var(--rule);
  font-size:12.5px;color:var(--muted);}
footer b{color:var(--ink-2);}
@media (max-width:760px){.wrap{padding:26px 14px 60px;} h1{font-size:27px;}}
"""


def build(models: list[dict]) -> str:
    impl = [m for m in models if m.get("status") == "implemented"]
    checked = [m for m in impl if m.get("parity_status") in {"checked", "matched"}]
    src = Counter(m.get("open_source") for m in impl)
    by = defaultdict(lambda: defaultdict(list))
    for m in impl:
        by[m["disease"]][m["axis"]].append(m)

    gap_note = {}
    for m in models:
        if m.get("status") in {"gap", "catalog"}:
            gap_note.setdefault((m.get("disease"), m.get("axis")),
                                m.get("tier_note") or "")

    rows: list[str] = []
    for i, did in enumerate(sorted(DISEASE_LABEL, key=lambda k: DISEASE_LABEL[k])):
        band = " banded" if i % 2 else ""
        # One merged cell per disease spanning all of its rows, and one per
        # question spanning its models. Without this the eye reads three
        # unrelated rows instead of one disease asked three questions.
        disease_span = sum(max(1, len(by.get(did, {}).get(a, []))) for a in AXES)
        first = True
        for axis in AXES:
            entries = by.get(did, {}).get(axis, [])
            gs = " group-start" if first else ""
            dcell = (f'<td class="disease" rowspan="{disease_span}">'
                     f'{DISEASE_LABEL[did]}</td>' if first else "")
            acell = (f'<td class="axis" rowspan="{max(1, len(entries))}">'
                     f'{AXIS_LABEL[axis]}</td>')
            if not entries:
                note = e(gap_note.get((did, axis), ""))
                extra = f'<div class="gapnote">{note[:120]}</div>' if note else ""
                rows.append(
                    f'<tr class="empty{band}{gs}">{dcell}{acell}'
                    f'<td colspan="8"><span class="dash">&mdash;</span> '
                    f'<span class="gapnote">{GAP_CELL_LABEL}</span>'
                    f'{extra}</td></tr>')
                first = False
                continue
            for k, m in enumerate(entries):
                name = e(m["title"].split("(")[0].split("—")[0].strip())
                osrc = m.get("open_source")
                note = e(m.get("parity_note"))
                short = note.split(". ")[0]
                if len(short) < 45 and ". " in note:
                    short = ". ".join(note.split(". ")[:2])
                if len(short) > 190:
                    short = short[:189].rsplit(" ", 1)[0] + "…"
                ev = m.get("evidence") or {}
                fn = ev.get("test_function")
                repro = ['<div class="repro"><span>reproduce it</span><ul>']
                if ev.get("test"):
                    repro.append(f'<li><code>pytest {e(ev["test"])}'
                                 + (f'::{e(fn)}' if fn else '') + '</code></li>')
                if ev.get("script"):
                    repro.append(f'<li>captured by <code>{e(ev["script"])}</code></li>')
                if ev.get("fixture"):
                    repro.append(f'<li>fixture <code>{e(ev["fixture"])}</code></li>')
                repro.append('</ul></div>')
                more = ('<details><summary>full evidence</summary>'
                        f'<p>{note}</p>{"".join(repro)}</details>')
                repo = m.get("public_repo")
                source_url = m.get("source_url") or ""
                src_label = (source_url.replace("https://doi.org/", "doi:")
                             .replace("https://pubmed.ncbi.nlm.nih.gov/", "PMID ")
                             .rstrip("/"))
                repo_cell = (
                    f'<a href="{e(repo)}">{e(repo.rstrip("/").split("/")[-1])}</a>'
                    if repo else '<span class="dash">&mdash;</span>')
                rows.append(
                    f'<tr class="{band.strip()}{gs if k == 0 else ""}">'
                    f'{dcell if k == 0 else ""}'
                    f'{acell if k == 0 else ""}'
                    f'<td class="model">{name}</td>'
                    f'<td class="repo">{repo_cell}<br>'
                    f'<span class="chip {SOURCE_CLASS.get(osrc, "")}">'
                    f'{SOURCE_LABEL.get(osrc, "")}</span></td>'
                    f'<td class="cite"><a href="{e(source_url)}">{e(src_label)}</a><br>'
                    f'{e(m.get("citation"))}</td>'
                    f'<td class="arch"><span class="fam">'
                    f'{e(m.get("architecture_family"))}</span>'
                    f'<div class="archline">{e(m.get("architecture"))}</div></td>'
                    f'<td class="formula"><pre>'
                    f'{html.escape(str(m.get("core_formula") or ""))}</pre></td>'
                    f'<td class="year">{m.get("year", "")}</td>'
                    + '<td class="perf">'
                    + (f'<div class="disc">{e(m.get("discrimination"))}</div>'
                       if m.get("discrimination")
                       else '<div class="unrec">we have not read this from the '
                            'paper yet</div>')
                    + (f'<div class="coh">Built on {e(m.get("development_cohort"))}</div>'
                       if m.get("development_cohort") else '')
                    + '</td>'
                    f'<td class="verified"><span class="chip ok">verified</span>'
                    f'<div class="how">{short}</div>{more}</td></tr>')
                first = False

    return f"""<title>CancerVerse &mdash; coverage</title>
<style>{CSS}</style>
<div class="wrap">
<header>
  <div class="eyebrow">M31 Biomedical AI &middot; classical baselines</div>
  <h1>Every disease, every question, every model</h1>
  <p class="sub">Published clinical risk equations reimplemented in Python. Each
  row records where the equation came from, what kind of model it is, its core
  formula, and how the implementation was checked against a source we did not
  write.</p>
  <div class="stats">
    <div class="stat"><b>{len(by)} / 12</b><span>diseases covered</span></div>
    <div class="stat"><b>{len(impl)}</b><span>models implemented</span></div>
    <div class="stat"><b>{len(checked)} / {len(impl)}</b><span>independently verified</span></div>
    <div class="stat"><b>{src['web_only'] + src['none']}</b><span>had no reference code</span></div>
  </div>
  <p class="note"><b>Not for clinical use.</b> A research artifact, not a medical
  device. Every model carries its own population and scope; applied outside it,
  the number looks valid and is not.</p>
</header>

<div class="scroller">
<table>
  <thead><tr>
    <th>Disease</th><th>Question</th><th>Model</th>
    <th>Public repository</th><th>Source</th><th>Architecture</th>
    <th>Core formula</th><th>Year</th><th>How well it discriminates</th>
    <th>Verified &mdash; how</th>
  </tr></thead>
  <tbody>
{chr(10).join(rows)}
  </tbody>
</table>
</div>

<footer>
  <b>Public repository</b> links the code we diffed against, where one exists.
  <b>Source</b> links the publication &mdash; every model has one, and it is the
  thing to check us against.
  <br><br>
  <b>How hard it was to get.</b> <span class="chip src-code">public code</span>
  a runnable implementation we could diff against &nbsp;
  <span class="chip src-web">web calculator only</span> the maths lived on
  someone else's server &nbsp;
  <span class="chip src-paper">paper only</span> printed coefficients, sometimes
  as an image.
  <br><br>
  {GAP_CAPTION}
  Generated from <code style="display:inline">registry/models.yaml</code>.
</footer>
</div>
"""


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "coverage.html"
    models = yaml.safe_load(REGISTRY.read_text())["models"]
    out.write_text(build(models))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
