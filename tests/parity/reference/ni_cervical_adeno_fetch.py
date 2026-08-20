"""Capture the Ni 2021 cervical-adenocarcinoma model from the authors' Shiny app.

This script produced two committed artifacts and is kept so both can be
re-derived:

    ni_cervical_adeno_model_summary.txt   the `survival::coxph` printout
    ni_cervical_adeno_cases.json          33 predictions, the parity fixture

Run it only to refresh them. The tests are offline and read the files.

    python tests/parity/reference/ni_cervical_adeno_fetch.py

What the paper does and does not publish
----------------------------------------
Ann Transl Med 2021;9(4):293 (doi:10.21037/atm-20-6201, PMC7944266) prints the
multivariable hazard ratios with reference categories (Table 3) and the
nomogram as Figure 3. Like every other cervical prognosis nomogram this project
has examined, it never prints a baseline survival function, so the points ->
probability step exists only as a drawn axis. The article alone can rank
patients; it cannot state a probability.

Two things the authors' own deployed calculator supplies:

1. **The coefficients**, to five decimal places, from the "Model Summary" tab,
   `DynNom` wires that panel to a renderPrint of the fitted object, and for a
   `survival::coxph` fit R's print method emits the whole coefficient table.
   This is `docs/EXTRACTION.md` Route A3.

2. **The baseline survival S0(t)**, which the Model Summary does NOT contain,
   for a Cox fit the baseline is a separate object from the coefficients. It is
   recovered here by Route B, one deliberate probe: set every covariate to its
   own reference level (grade I, T1a, N0, M0, no surgery, tumour <=20 mm), at
   which Xb = 0 by construction, so the returned survival probability *is*
   S0(t). Six horizons are captured this way.

The remaining cases each move exactly one covariate off that reference, which
makes every coefficient individually falsifiable: S(t) must equal
S0(t) ** exp(beta) for that one term and nothing else.

Precision, and why the baseline needs more than one probe
---------------------------------------------------------
`DynNom` reports **two significant figures**. Read at the reference pattern
that pins S0 only to +/-0.005, and this model's exponent runs to exp(5.36) =
213, so +/-0.005 on S0 is a factor of nine on the sickest patient. Two probes
therefore are not enough.

The fix is the same one used for the Kunzmann divisor (docs/EXTRACTION.md,
"When the sources disagree"): every reported probability is a *constraint* on
S0, and a high-risk pattern constrains it hard, because two significant figures
on p give S0 = p^(1/213) to a few parts in 100,000. Twelve high-risk patterns
are captured for that purpose and the accepted S0 is the intersection of all
the intervals, checked for non-emptiness. The script reads the plotly payload
behind the "Predicted Survival" tab (`plot2`) rather than the Numerical Summary
table because plotly carries the raw number rather than a re-formatted string;
both round to two significant figures, and that is the app's limit, not the
transport's.

Talking to a Shiny app from a script
------------------------------------
See tests/parity/reference/wang_larc_pcr_fetch.py, which documents the SockJS /
robust / multiplex framing, the transient cold-start shell, and the suspended-
hidden-output trap. Three differences here:

- the app lives at `/dynnomapp/`, so every path parameter changes;
- the output of interest is `plot2` (plotly), not `data.pred`, and plotly
  outputs stay suspended unless the client also supplies
  `.clientdata_output_plot2_{width,height,bg,fg,accent,font}`;
- shinyapps.io answered HTTP 500 to the container page under repeated hits.
  Back off and retry; it is a per-instance limit, not a rejection.

Requires `websocket-client`, which is not a dependency of this package; the
tests do not need it.
"""

from __future__ import annotations

import http.cookiejar
import json
import random
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import websocket  # pip install websocket-client

APP = "https://betteryuan66.shinyapps.io/dynnomapp/"
HOST = "betteryuan66.shinyapps.io"
PATH = "/dynnomapp/"
HERE = Path(__file__).parent
UA = "Mozilla/5.0 Chrome/120"

OUTPUTS = ("manySliders", "setlimits", "plot", "plot2", "data.pred", "summary")

#: Every covariate at its own reference level, so Xb = 0 and the app returns
#: the baseline survival itself.
REFERENCE = {
    "grade": "grade I",
    "stage_T": "T1a",
    "stage_N": "N0",
    "stage_M": "M0",
    "surg_prim": "no",
    "tumor_size": "<=20mm",
}

#: (label, covariates changed from REFERENCE, follow-up months)
CASES: list[tuple[str, dict, int]] = [
    # S0(t): six horizons at the reference covariate pattern.
    ("baseline_12m", {}, 12),
    ("baseline_24m", {}, 24),
    ("baseline_36m", {}, 36),
    ("baseline_48m", {}, 48),
    ("baseline_60m", {}, 60),
    ("baseline_120m", {}, 120),
    # One covariate off reference at a time: eleven cases, eleven coefficients.
    ("grade_II", {"grade": "grade II"}, 60),
    ("grade_III_IV", {"grade": "grade III and IV"}, 60),
    ("T1b", {"stage_T": "T1b"}, 60),
    ("T2", {"stage_T": "T2"}, 60),
    ("T3", {"stage_T": "T3"}, 60),
    ("T4", {"stage_T": "T4"}, 60),
    ("N1", {"stage_N": "N1"}, 60),
    ("M1", {"stage_M": "M1"}, 60),
    ("surgery", {"surg_prim": "yes"}, 60),
    ("size_21_40mm", {"tumor_size": "21-40mm"}, 60),
    ("size_gt40mm", {"tumor_size": ">40mm"}, 60),
    # Combinations, including both extremes of the risk range.
    ("worst_60m", {"grade": "grade III and IV", "stage_T": "T4",
                   "stage_N": "N1", "stage_M": "M1",
                   "tumor_size": ">40mm"}, 60),
    ("worst_36m", {"grade": "grade III and IV", "stage_T": "T4",
                   "stage_N": "N1", "stage_M": "M1",
                   "tumor_size": ">40mm"}, 36),
    ("best_60m", {"surg_prim": "yes"}, 60),
    ("mixed_60m", {"grade": "grade II", "stage_T": "T2", "stage_N": "N1",
                   "surg_prim": "yes", "tumor_size": "21-40mm"}, 60),
    # High-risk probes, used only to pin S0 down. The app reports two
    # significant figures; at the reference pattern that leaves S0 known only
    # to +/-0.005, which is useless. Each of these has exp(Xb) of 100-200, so
    # the same two figures constrain S0 to a few parts in 100,000, and the
    # intersection of several independent constraints is tighter still. Same
    # technique as the Kunzmann divisor in docs/EXTRACTION.md.
    ("high_a_36m", {"grade": "grade III and IV", "stage_T": "T3",
                    "stage_N": "N1", "stage_M": "M1",
                    "tumor_size": ">40mm"}, 36),
    ("high_b_36m", {"grade": "grade III and IV", "stage_T": "T4",
                    "stage_N": "N1", "stage_M": "M1",
                    "tumor_size": "21-40mm"}, 36),
    ("high_c_36m", {"grade": "grade III and IV", "stage_T": "T4",
                    "stage_N": "N1", "stage_M": "M0",
                    "tumor_size": ">40mm"}, 36),
    ("high_d_36m", {"grade": "grade III and IV", "stage_T": "T4",
                    "stage_N": "N0", "stage_M": "M1",
                    "tumor_size": ">40mm"}, 36),
    ("high_e_36m", {"grade": "grade II", "stage_T": "T4", "stage_N": "N1",
                    "stage_M": "M1", "tumor_size": ">40mm"}, 36),
    ("high_f_36m", {"grade": "grade III and IV", "stage_T": "T3",
                    "stage_N": "N1", "stage_M": "M1",
                    "tumor_size": "21-40mm"}, 36),
    ("high_a_60m", {"grade": "grade III and IV", "stage_T": "T3",
                    "stage_N": "N1", "stage_M": "M1",
                    "tumor_size": ">40mm"}, 60),
    ("high_b_60m", {"grade": "grade III and IV", "stage_T": "T4",
                    "stage_N": "N1", "stage_M": "M1",
                    "tumor_size": "21-40mm"}, 60),
    ("high_c_60m", {"grade": "grade III and IV", "stage_T": "T4",
                    "stage_N": "N1", "stage_M": "M0",
                    "tumor_size": ">40mm"}, 60),
    ("high_d_60m", {"grade": "grade III and IV", "stage_T": "T4",
                    "stage_N": "N0", "stage_M": "M1",
                    "tumor_size": ">40mm"}, 60),
    ("high_e_60m", {"grade": "grade II", "stage_T": "T4", "stage_N": "N1",
                    "stage_M": "M1", "tumor_size": ">40mm"}, 60),
    ("high_f_60m", {"grade": "grade III and IV", "stage_T": "T3",
                    "stage_N": "N1", "stage_M": "M1",
                    "tumor_size": "21-40mm"}, 60),
]


def _rnd(n: int) -> str:
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(alphabet) for _ in range(n))


class ShinySession:
    """A scripted Shiny client: SockJS + robust + multiplex + Shiny."""

    def __init__(self, attempts: int = 15) -> None:
        cj = http.cookiejar.CookieJar()
        self.http = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj)
        )
        self.http.addheaders = [("User-Agent", UA)]

        worker = None
        for _ in range(attempts):
            try:
                body = self.http.open(APP).read().decode()
            except Exception:  # shinyapps.io 500s under repeated hits
                time.sleep(20)
                continue
            match = re.search(r"_w_([0-9a-f]+)", body)
            if match:
                worker = match.group(1)
                break
            time.sleep(4)  # still the cold-start shell
        if worker is None:
            raise RuntimeError("app never left the loading shell")

        token = self.http.open(APP + "__token__").read().decode().strip()
        cookies = "; ".join(f"{c.name}={c.value}" for c in cj)
        url = (
            f"wss://{HOST}{PATH}__sockjs__/n={_rnd(8)}/t={token}/w={worker}"
            f"/s=0/{random.randint(100, 999)}/{_rnd(8)}/websocket"
        )
        self.ws = websocket.create_connection(
            url, timeout=30,
            header=[f"Cookie: {cookies}", f"User-Agent: {UA}"],
            origin=f"https://{HOST}",
            sslopt={"cert_reqs": ssl.CERT_NONE},
        )
        assert self.ws.recv() == "o", "SockJS did not open"
        self._out_id = 0
        self._send_raw("0|o|")  # open multiplex channel 0

    def _send_raw(self, payload: str) -> None:
        self.ws.send(json.dumps([f"{self._out_id:X}#{payload}"]))
        self._out_id += 1

    def send(self, message: dict) -> None:
        self._send_raw("0|m|" + json.dumps(message))

    def pump(self, seconds: float = 10.0) -> list:
        """Collect Shiny messages, unwrapping all three framing layers."""
        messages: list = []
        end = time.time() + seconds
        self.ws.settimeout(2)
        while time.time() < end:
            try:
                frame = self.ws.recv()
            except Exception:
                continue
            if not frame or frame[0] != "a":
                continue
            for tagged in json.loads(frame[1:]):
                body = re.sub(r"^[\dA-F]+#", "", tagged)
                inner = re.match(r"^\d+\|[moc]\|([\s\S]*)$", body)
                try:
                    messages.append(json.loads(inner.group(1) if inner else body))
                except (AttributeError, ValueError):
                    continue
        return messages

    def init(self) -> list:
        data = {
            ".clientdata_pixelratio": 1,
            ".clientdata_url_protocol": "https:",
            ".clientdata_url_hostname": HOST,
            ".clientdata_url_port": "",
            ".clientdata_url_pathname": PATH,
            ".clientdata_url_search": "",
            ".clientdata_url_hash": "",
            ".clientdata_url_hash_initial": "",
            ".clientdata_singletons": "",
            ".clientdata_allowDataUriScheme": True,
            ".clientdata_output_plot_width": 800,
            ".clientdata_output_plot_height": 400,
            # plotly reports its own size/theme; without these six the widget
            # never renders and `plot2` never arrives.
            ".clientdata_output_plot2_width": 800,
            ".clientdata_output_plot2_height": 400,
            ".clientdata_output_plot2_bg": "#FFFFFF",
            ".clientdata_output_plot2_fg": "#000000",
            ".clientdata_output_plot2_accent": "#337AB7",
            ".clientdata_output_plot2_font": {
                "families": ["sans-serif"], "size": "14px",
            },
            # DynNom wires Quit to stopApp(); without these two the R session
            # exits before it answers anything.
            "quit": 0,
            "add": 0,
        }
        for name in OUTPUTS:
            # `plot` is a base-R survival-curve image we do not need and the
            # slowest thing the app renders.
            data[f".clientdata_output_{name}_hidden"] = name == "plot"
        self.send({"method": "init", "data": data})
        return self.pump(30)


def _value(messages: list, key: str):
    found = None
    for m in messages:
        if isinstance(m, dict) and key in m.get("values", {}):
            found = m["values"][key]
    return found


def _prediction(widget: dict) -> tuple[float, float, float]:
    """Pull point estimate and CI out of the plotly payload (4 dp)."""
    # The widget is cumulative, exactly like the Numerical Summary table: each
    # press of Predict appends a point. The case just submitted is the last.
    trace = widget["x"]["data"][0]
    point = float(trace["x"][-1])
    # At the very low-risk end the app's CI collapses onto the point estimate
    # and plotly drops the error bars entirely.
    err = trace.get("error_x")
    if not err:
        return point, point, point
    upper = point + float(err["array"][-1])
    lower = point - float(err["arrayminus"][-1])
    return point, lower, upper


def main() -> None:
    session = ShinySession()
    startup = session.init()
    summary = _value(startup, "summary")
    if not summary:
        raise RuntimeError("no Model Summary returned")
    (HERE / "ni_cervical_adeno_model_summary.txt").write_text(summary)

    rows = []
    for i, (label, overrides, months) in enumerate(CASES, start=1):
        inputs = dict(REFERENCE)
        inputs.update(overrides)
        session.send({"method": "update", "data": {
            **inputs, "times": True, "tim": months,
        }})
        session.pump(2)
        # `add` is the Predict button: an actionButton, so it must INCREASE.
        session.send({"method": "update", "data": {"add": i}})
        widget = _value(session.pump(15), "plot2")
        if widget is None:
            raise RuntimeError(f"case {label} returned no prediction")
        point, lower, upper = _prediction(widget)
        rows.append({
            "label": label,
            "months": months,
            **inputs,
            "prediction": point,
            "lower_bound": lower,
            "upper_bound": upper,
        })
        print(f"{label}: {point}")
        time.sleep(2.0)

    (HERE / "ni_cervical_adeno_cases.json").write_text(json.dumps({
        "source": APP,
        "tool": "Ni 2021 dynamic nomogram for cancer-specific survival in "
                "uterine cervical adenocarcinoma (R/Shiny, DynNom, coxph)",
        "supporting_publication": "Ni X, Ma X, Qiu J, et al. Ann Transl Med. "
                                  "2021;9(4):293, PMCID PMC7944266 - the app "
                                  "URL is printed in the article",
        "captured": time.strftime("%Y-%m-%d"),
        "resolution": "2 significant figures, the app's own rounding. Read "
                      "from the plotly payload behind the Predicted Survival "
                      "tab; the Numerical Summary table carries the same "
                      "rounding.",
        "capture_script": "ni_cervical_adeno_fetch.py",
        "cases": rows,
    }, indent=2) + "\n")
    print(f"captured {len(rows)} cases and the model summary")


if __name__ == "__main__":
    sys.exit(main())
