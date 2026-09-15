"""The claims ledger, structurally guarded (`docs/claims.md`).

The ledger is prose, so a test cannot check that its readings are right — that is what the
measurements in `runs/levers_10seeds.json` and the review in `docs/validation.md` are for.
What a test *can* stop is the ways this file rots: a claim quietly losing its verdict, a
verdict word drifting into something vaguer, a lever being renamed in the code while the
ledger goes on citing it, or the ledger starting to report magnitudes that phase E's variance
rule says the model may not report.
"""

import re
from pathlib import Path

import pytest

from resim.cli import LEVERS, PATHS

LEDGER = Path(__file__).resolve().parents[1] / "docs" / "claims.md"
VERDICTS = ("supported", "contradicted", "conditional", "unidentifiable")


@pytest.fixture(scope="module")
def ledger() -> str:
    return LEDGER.read_text(encoding="utf-8")


def test_every_claim_has_a_verdict(ledger):
    """A row without a verdict is a citation, not an adjudication."""
    claims = re.findall(r"^## (F-\d+) · (.+)$", ledger, flags=re.MULTILINE)
    assert len(claims) >= 10, "the ledger should carry the claims the summary table lists"
    sections = re.split(r"^## (?=F-\d+ ·)", ledger, flags=re.MULTILINE)[1:]
    for section in sections:
        head = section.splitlines()[0]
        assert "**Verdict" in section, f"no verdict in {head}"
        verdict_line = section[section.index("**Verdict") :][:200].lower()
        assert any(word in verdict_line for word in VERDICTS), f"unrecognised verdict in {head}"


def test_the_summary_table_covers_every_claim(ledger):
    """The table at the top is the index; a claim missing from it is a claim nobody finds."""
    in_sections = set(re.findall(r"^## (F-\d+) ·", ledger, flags=re.MULTILINE))
    in_table = set(re.findall(r"^\| (F-\d+) \|", ledger, flags=re.MULTILINE))
    assert in_sections <= in_table, f"missing from the summary: {in_sections - in_table}"


def test_every_lever_the_ledger_cites_still_exists(ledger):
    """A renamed lever must break here rather than leave the ledger quoting a dead scenario."""
    cited = set(
        re.findall(
            r"`(rent-cap|transaction-tax|vacancy-tax|public-housing|"
            r"tourist-restriction|demand-subsidy|land-release|credit-crunch|"
            r"labour-shock)`",
            ledger,
        )
    )
    known = set(LEVERS) | set(PATHS)
    assert cited <= known, f"the ledger cites levers the CLI does not have: {cited - known}"


def test_the_ledger_states_the_reporting_rule(ledger):
    """A ledger that forgets the reporting contract is a forecast sheet.

    Updated 2026-09-15: the rule itself moved. Phase E left two reportable magnitudes and the
    guard pinned their names; after §5c.8 the set is larger and the RENT side is what is now
    direction-only, so pinning "ownership rate and arrears" would pin a statement that is no
    longer true. What the guard checks is what cannot go stale: that the ledger cites the rule,
    says which side of the model may not be reported as a magnitude, and names the parameter
    that decides it.
    """
    assert "§13.2" in ledger or "13.2" in ledger
    assert "direction" in ledger.lower()
    assert "small_landlord_premium" in ledger, "the rent side's binding parameter is unnamed"
    assert "conditional on the sourced parameter bands" in ledger


def test_seed_counts_are_shown_for_model_responses(ledger):
    """Ten seeds, per §13.4, and the sign count is what makes a direction claim checkable."""
    assert "10/10" in ledger
    assert re.search(r"5/10|6/10", ledger), "the ledger must show which responses are noise"
    assert "no effect" in ledger


def test_the_ledger_says_what_it_cannot_do(ledger):
    """The distinction between 'false' and 'nobody can know this' is the model's sharpest
    output (redesign spec §1), so the ledger has to carry its own limits."""
    tail = ledger[ledger.index("## What this ledger cannot do") :]
    assert "hold-out is spent" in tail
    assert "quality" in tail.lower()
    assert len(tail.splitlines()) >= 8
