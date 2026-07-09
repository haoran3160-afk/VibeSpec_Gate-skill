from vibespec_gate.core.gate_decision import decide_gate
from vibespec_gate.core.risk_model import Finding


def test_gate_blocks_on_p0():
    summary = decide_gate([Finding(id="VSG-X", title="x", severity="P0", category="Secrets")])
    assert summary["decision"] == "BLOCK"
