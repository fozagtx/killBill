"""Run the audit pipeline and dump the result to web/demo_report.json
so the web UI has a fast-loading offline fallback."""
import json
import os
import sys
from pathlib import Path

# We import the Jac module the Python way — jaclang registers a Python import
# hook that compiles `.jac` files on demand.
import jaclang  # noqa: F401  (side-effect: registers importer)

from audit import audit_statement_path

if __name__ == "__main__":
    csv = sys.argv[1] if len(sys.argv) > 1 else "samples/statement_001.csv"
    out_path = Path(__file__).resolve().parent.parent / "web" / "demo_report.json"
    rep = audit_statement_path(csv)
    out_path.write_text(json.dumps(rep, indent=2))
    print(f"wrote {out_path} ({len(rep.get('subscriptions', []))} subs, "
          f"${rep.get('monthly_savings', 0):.2f}/mo savings)")
