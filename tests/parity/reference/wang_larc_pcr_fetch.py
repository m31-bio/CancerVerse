"""Capture the Wang 2024 pCR nomogram from the authors' own Shiny calculator.

This script produced two committed artifacts and is kept so both can be
re-derived:

    wang_larc_pcr_model_summary.txt   the `rms::lrm` printout. THE EQUATION
    wang_larc_pcr_cases.json          13 predictions, the parity fixture

Run it only to refresh them. The tests are offline and read the files.

    python tests/parity/reference/wang_larc_pcr_fetch.py

Why this is Route A and not Route B
-----------------------------------
Cancer Med 2024;13(11):e7251 publishes odds ratios (Table 4) and a nomogram
*points* formula (Results 3.3) but no intercept and no points-to-probability
axis outside Figure 3A, so the article cannot produce a probability. There is
no supplement ("All data ... are included within the article"), no erratum and
no source release.

The authors' deployed app is built with R's `DynNom`, which ships a "Model
Summary" tab wired to `output$summary <- renderPrint(summary/print of the
model object)`. For an `rms::lrm` fit that prints the whole coefficient table,
intercept included. So the tool hands over the MODEL, not one output per
request, `docs/EXTRACTION.md` Route A. The 13 probed cases are then a
consistency check on the transcription rather than the source of the model.

Talking to a Shiny app from a script, the parts that cost time
---------------------------------------------------------------
`docs/EXTRACTION.md` previously recorded Shiny as unreachable ("keeps the model
server-side and talks over a websocket; the page returns a loading shell").
Both halves are true and neither is fatal. What it takes:

1. **The loading shell is transient.** shinyapps.io answers HTTP 202 with a
   4.5 KB frame while the container cold-starts, then serves the real app HTML
   at the same URL. Re-request until `_w_<workerId>` appears in the body. A
   single fetch that returns the shell proves nothing.

2. **The SockJS endpoint is parameterised.** `shiny-server-client` builds
   `<app>/__sockjs__/` and then appends path params in the fixed order
   n, o, t, w, s (see its `reorderPathParams`). All of n= (a fresh robust-
   connection id), t= (a token from `GET <app>/__token__`) and w= (the worker
   id from the page) are required; omit any and the router 404s.

3. **Three framing layers, outermost first.** SockJS (`["<payload>"]` out,
   `a[...]` in), then the robust layer (`<hex-msg-id>#<payload>`), then the
   multiplexer (`<channel>|m|<payload>`, with `<channel>|o|<relUrl>` to open).
   Shiny's own JSON is the innermost payload.

4. **Send `quit` and `add` in the init message.** Without them the R session
   dies immediately with SockJS close code 4702 and no error text, `DynNom`
   wires the Quit button straight to `stopApp()`. This looked exactly like a
   rejected handshake and was the only genuinely obscure step.

5. **Hidden outputs are suspended.** Shiny will not compute `summary` unless
   the client asserts `.clientdata_output_summary_hidden: false`. The Model
   Summary tab is behind a tabsetPanel, so a browser-faithful client would
   never receive it.

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

APP = "https://pcrpredict.shinyapps.io/LARC2/"
HOST = "pcrpredict.shinyapps.io"
HERE = Path(__file__).parent
UA = "Mozilla/5.0 Chrome/120"

#: Deliberately chosen: every case differs from the reference patient in
#: exactly one covariate, plus both ends of the CEA slider, plus the two
#: extremes. That straddles all four T levels, all three N levels and every
#: binary, so no single coefficient can be wrong and still pass.
CASES = [
    ("cN0", "cT2", "Negative", "No", "Adenocarcinoma", 0),
    ("cN0", "cT2", "Negative", "No", "Adenocarcinoma", 24),
    # the pivot every one-covariate-at-a-time case below is compared against
    ("cN0", "cT2", "Negative", "No", "Adenocarcinoma", 5),
    ("cN1", "cT2", "Negative", "No", "Adenocarcinoma", 5),
    ("cN2", "cT2", "Negative", "No", "Adenocarcinoma", 5),
    ("cN0", "cT3", "Negative", "No", "Adenocarcinoma", 5),
    ("cN0", "cT4", "Negative", "No", "Adenocarcinoma", 5),
    ("cN0", "cTcT1", "Negative", "No", "Adenocarcinoma", 5),
    ("cN0", "cT2", "Positive", "No", "Adenocarcinoma", 5),
    ("cN0", "cT2", "Negative", "Yes", "Adenocarcinoma", 5),
    ("cN0", "cT2", "Negative", "No",
     "Signet-ring cell carcinoma/Mucinous adenocarcinoma", 5),
    ("cN2", "cT4", "Positive", "No",
     "Signet-ring cell carcinoma/Mucinous adenocarcinoma", 24),
    ("cN0", "cTcT1", "Negative", "Yes", "Adenocarcinoma", 0),
]

OUTPUTS = ("manySliders", "setlimits", "plot", "data.pred", "summary")


def _rnd(n: int) -> str:
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(alphabet) for _ in range(n))


class ShinySession:
    """A scripted Shiny client: SockJS + robust + multiplex + Shiny."""

    def __init__(self, attempts: int = 10) -> None:
        cj = http.cookiejar.CookieJar()
        self.http = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj)
        )
        self.http.addheaders = [("User-Agent", UA)]

        worker = None
        for _ in range(attempts):
            body = self.http.open(APP).read().decode()
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
            f"wss://{HOST}/LARC2/__sockjs__/n={_rnd(8)}/t={token}/w={worker}"
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

    def pump(self, seconds: float = 10.0) -> list[dict]:
        """Collect Shiny messages, unwrapping all three framing layers."""
        messages: list[dict] = []
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

    def init(self) -> list[dict]:
        data = {
            ".clientdata_pixelratio": 1,
            ".clientdata_url_protocol": "https:",
            ".clientdata_url_hostname": HOST,
            ".clientdata_url_port": "",
            ".clientdata_url_pathname": "/LARC2/",
            ".clientdata_url_search": "",
            ".clientdata_url_hash": "",
            ".clientdata_url_hash_initial": "",
            ".clientdata_singletons": "",
            ".clientdata_allowDataUriScheme": True,
            ".clientdata_output_plot_width": 800,
            ".clientdata_output_plot_height": 400,
            # DynNom wires Quit to stopApp(); without these two the R session
            # exits before it answers anything. See note 4 in the docstring.
            "quit": 0,
            "add": 0,
            "tabs": "Numerical Summary",
        }
        for name in OUTPUTS:
            # `plot` stays hidden: it is a plotly widget we do not need and it
            # is the slowest thing the app renders.
            data[f".clientdata_output_{name}_hidden"] = name == "plot"
        self.send({"method": "init", "data": data})
        return self.pump(25)


def _values(messages: list[dict], key: str):
    for m in messages:
        if isinstance(m, dict) and key in m.get("values", {}):
            return m["values"][key]
    return None


def main() -> None:
    session = ShinySession()
    startup = session.init()
    summary = _values(startup, "summary")
    if not summary:
        raise RuntimeError("no Model Summary returned")
    (HERE / "wang_larc_pcr_model_summary.txt").write_text(summary)

    rows = []
    for i, (n, t, emvi, tnt, histology, cea) in enumerate(CASES, start=1):
        session.send({"method": "update", "data": {
            "pred1": n, "pred2": t, "pred3": emvi,
            "pred4": tnt, "pred5": histology, "pred6": cea,
        }})
        session.pump(2)
        # `add` is the Predict button: an actionButton, so it must INCREASE.
        session.send({"method": "update", "data": {"add": i}})
        table = _values(session.pump(12), "data.pred")
        if table is None:
            raise RuntimeError(f"case {i} returned no prediction")
        # The Numerical Summary table is cumulative; the last row is this case.
        last = [ln for ln in table.splitlines() if re.match(r"^\s*\d+\s", ln)][-1]
        prediction, lower, upper = (float(v) for v in last.split()[-3:])
        rows.append({
            "n_stage": n, "t_stage": t, "mri_emvi": emvi, "tnt": tnt,
            "histopathology": histology, "cea_ng_ml": float(cea),
            "prediction": prediction, "lower_bound": lower, "upper_bound": upper,
        })
        time.sleep(1.5)

    (HERE / "wang_larc_pcr_cases.json").write_text(json.dumps({
        "source": APP,
        "tool": "Wang 2024 dynamic nomogram for pCR in locally advanced "
                "rectal cancer (R/Shiny, DynNom)",
        "supporting_publication": "Wang G, Li J, Huang Y, Guo Y. Cancer Med. "
                                  "2024;13(11):e7251, PMCID PMC11141331 - the "
                                  "app URL is printed in the article",
        "captured": time.strftime("%Y-%m-%d"),
        "resolution": "3 decimal places, as printed by the app's Numerical "
                      "Summary tab",
        "capture_script": "wang_larc_pcr_fetch.py",
        "cases": rows,
    }, indent=2) + "\n")
    print(f"captured {len(rows)} cases and the model summary")


if __name__ == "__main__":
    sys.exit(main())
