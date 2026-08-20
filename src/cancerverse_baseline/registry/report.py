"""Human-readable progress report. Run: python -m cancerverse_baseline.registry.report"""

from __future__ import annotations

from .load import AXES, coverage_matrix, load_diseases, progress_report

_BLOCKER_LABEL = {
    "needs_r_runtime": "run the open reference implementation (needs R)",
    "needs_web_calculator": "enter our inputs into the canonical web tool",
    "no_published_example": "nothing to reproduce — no worked example exists",
    "unclassified": "UNCLASSIFIED — blocker not recorded",
}


def render() -> str:
    r = progress_report()
    diseases = load_diseases()
    matrix = coverage_matrix()
    out: list[str] = []
    w = out.append

    w("CancerVerse — coverage")
    w("=" * 62)
    w("")
    w(f"  Cells implemented   {r['n_cells_implemented']:>3} / {r['n_cells_reachable']:<3} reachable"
      f"   ({r['pct_of_reachable']:.0f}%)")
    w(f"  ...of the nominal   {r['n_cells_implemented']:>3} / {r['n_cells_nominal']:<3} grid"
      f"        ({r['pct_of_nominal']:.0f}%)")
    w(f"  Not yet reachable   {r['n_cells_unreachable']:>3}"
      "      cells where we have not found a published equation yet")
    w("")
    w(f"  Models implemented  {r['n_models_implemented']:>3}")
    w(f"  Parity matched      {r['n_models_matched']:>3}"
      f"        ({r['pct_models_matched']:.0f}% of implemented)")
    w("")

    w("Per axis (implemented / reachable, unreachable excluded)")
    w("-" * 62)
    for axis in AXES:
        a = r["by_axis"][axis]
        pct = 100.0 * a["implemented"] / a["reachable"] if a["reachable"] else 0.0
        bar = "#" * int(pct / 5)
        w(f"  {axis:10} {a['implemented']:>2}/{a['reachable']:<2} {pct:>3.0f}%  {bar:<20}"
          f" ({a['unreachable']} unreachable)")
    w("")

    w("Coverage matrix")
    w("-" * 62)
    header = f"  {'disease':12}" + "".join(f"{a:<12}" for a in AXES)
    w(header)
    tiers = {(d, a): t for (d, a), t in __import__(
        "cancerverse_baseline.registry.load", fromlist=["cell_tiers"]
    ).cell_tiers().items()}
    for d in diseases:
        row = [f"  {d['id']:12}"]
        for axis in AXES:
            cell = matrix[d["id"]][axis]
            status = cell.get("status") if cell else None
            parity = cell.get("parity_status") if cell else None
            if status == "implemented":
                mark = "DONE*" if parity in {"checked", "matched"} else "done"
            elif tiers.get((d["id"], axis)) == "D":
                mark = "--"
            else:
                mark = f"todo({tiers.get((d['id'], axis), '?')})"
            row.append(f"{mark:<12}")
        w("".join(row))
    w("")
    w("  DONE* = implemented and parity-matched;  -- = no published equation found yet")
    w("")

    w(f"Remaining reachable cells ({r['n_cells_remaining']})")
    w("-" * 62)
    for disease, axis in r["remaining_cells"]:
        w(f"  {disease:12} {axis}")
    w("")

    w("What blocks parity on the implemented models")
    w("-" * 62)
    for blocker, ids in r["parity_blockers"].items():
        w(f"  {_BLOCKER_LABEL.get(blocker, blocker)}  [{len(ids)}]")
        for i in ids:
            w(f"      {i}")
    return "\n".join(out)


if __name__ == "__main__":
    print(render())
