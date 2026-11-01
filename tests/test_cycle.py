"""Behavioral checks for the work gate, not tests of whether a game is fun."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_cycle.py"


class CycleTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "assets" / "iteration.example.json").read_text())

    def check(self, record=None, previous=None, raw=None):
        self.assertTrue(CHECKER.is_file(), "Cycle checker is not implemented")
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "state.json"
            path.write_text(raw if raw is not None else json.dumps(record or self.record))
            cmd = [sys.executable, str(CHECKER), str(path)]
            if previous is not None:
                old = Path(directory) / "previous.json"
                old.write_text(json.dumps(previous))
                cmd += ["--previous", str(old)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotIn("Traceback", result.stderr)
            return result.returncode, json.loads(result.stdout)

    def valid(self, **kwargs):
        code, output = self.check(**kwargs)
        self.assertEqual(code, 0, output)
        self.assertTrue(output["record_valid"])

    def invalid(self, contains, **kwargs):
        code, output = self.check(**kwargs)
        self.assertNotEqual(code, 0)
        self.assertIn(contains, " ".join(output["errors"]))

    def ready(self):
        r = self.record
        r["findings"][0]["status"] = "resolved"
        r["findings"][0]["resolved_build"] = r["build"]
        r["evidence"] += [
            {"id": "H1", "build": r["build"], "kind": "human", "scopes": ["moment", "sequence", "whole"], "source": "fixture candidate observation", "observation": "Target player reports enjoyable tension, explains motive, prefers candidate"},
            {"id": "R1", "build": r["build"], "kind": "runtime", "scopes": ["moment", "sequence", "whole"], "source": "fixture candidate recording", "observation": "Continuous sequence and all relevant paths verified"},
            {"id": "H0", "build": "example-b13", "kind": "human", "scopes": ["moment", "sequence", "whole"], "source": "fixture baseline observation", "observation": "Target player comparison baseline"}
        ]
        for assessment in r["assessments"]:
            assessment.update(status="pass", evidence=["H1", "R1"])
        r["findings"][0]["evidence"] = ["R1"]
        r["comparison"] = {"baseline": "example-b13", "candidate": r["build"], "verdict": "better", "evidence": ["H0", "H1", "R1"], "tradeoffs": "No material loss found in tested scope", "conditions": "Comparable target players and same relevant sequence"}
        r["decision"] = "promote"
        r["next"] = None

    def test_core_experiment_allowed_with_human_enjoyment_unknown(self):
        self.valid()

    def test_polish_blocked_while_core_issue_open(self):
        self.record["next"]["kind"] = "polish"
        self.invalid("priority")

    def test_unrelated_task_blocked_even_when_called_experiment(self):
        self.record["next"]["addresses"] = []
        self.invalid("priority")

    def test_expression_fix_allowed_if_addresses_core(self):
        self.record["findings"][0]["aspect"] = "expression"
        self.record["next"]["change"] = "Restore contact animation needed to understand rescue"
        self.valid()

    def test_human_absence_does_not_freeze_development(self):
        self.record["next"]["kind"] = "collect"
        self.valid()

    def test_enjoyment_cannot_pass_on_ai_runtime_only(self):
        self.record["assessments"][0]["status"] = "pass"
        self.invalid("human")

    def test_prior_build_human_cannot_pass_current_enjoyment(self):
        self.ready()
        self.record["evidence"][1]["build"] = "old"
        self.invalid("current")

    def test_local_evidence_cannot_pass_whole(self):
        self.ready()
        self.record["evidence"][1]["scopes"] = ["moment"]
        self.invalid("scope")

    def test_missing_entire_enjoyment_dimension_is_rejected(self):
        self.record["assessments"] = [a for a in self.record["assessments"] if a["aspect"] != "enjoyment"]
        self.invalid("enjoyment")

    def test_stale_positive_evidence_cannot_pass_function(self):
        self.record["evidence"][0]["build"] = "old"
        self.record["assessments"][-1].update(status="pass", evidence=["E1"])
        self.invalid("current")

    def test_stale_negative_evidence_is_a_concern_not_current_failure(self):
        self.record["evidence"][0]["build"] = "old"
        self.record["assessments"][-1].update(status="fail", evidence=["E1"])
        self.invalid("current")

    def test_unknown_or_failure_blocks_promotion(self):
        self.record["decision"] = "promote"
        self.record["next"] = None
        self.invalid("promotion")

    def test_current_scoped_human_and_runtime_allow_bounded_promotion(self):
        self.ready()
        self.valid()

    def test_comparison_needs_actual_baseline_evidence(self):
        self.ready()
        self.record["comparison"]["evidence"] = ["H1", "R1"]
        self.invalid("baseline")

    def test_conflicting_fail_cannot_be_hidden_by_passing_duplicate(self):
        self.ready()
        a = copy.deepcopy(self.record["assessments"][0])
        a["status"] = "fail"
        self.record["assessments"].append(a)
        self.invalid("duplicate")

    def test_changed_quality_floor_rejected_against_previous(self):
        previous = copy.deepcopy(self.record)
        self.record["contract"]["quality_floor"] = ["Whatever current tools can do"]
        self.invalid("contract", previous=previous)

    def test_removed_unresolved_issue_rejected_against_previous(self):
        previous = copy.deepcopy(self.record)
        self.record["findings"] = []
        self.invalid("finding", previous=previous)

    def test_resolving_issue_requires_current_evidence(self):
        self.record["findings"][0].update(status="resolved", evidence=[])
        self.invalid("resolved")

    def test_finding_identity_cannot_be_replaced_with_unrelated_work(self):
        previous = copy.deepcopy(self.record)
        self.record["findings"][0].update(aspect="expression", observation="Title border needs polish")
        self.invalid("identity", previous=previous)

    def test_historical_resolution_survives_new_unrelated_build(self):
        self.record["findings"][0].update(status="resolved", resolved_build=self.record["build"])
        previous = copy.deepcopy(self.record)
        self.record["build"] = "example-b15"
        self.record["next"].update(kind="collect", addresses=[])
        self.valid(previous=previous)

    def test_new_resolution_cannot_use_old_build_evidence(self):
        previous = copy.deepcopy(self.record)
        self.record["build"] = "example-b15"
        self.record["findings"][0].update(status="resolved", resolved_build="example-b14")
        self.invalid("new resolution", previous=previous)

    def test_budget_blocks_starting_work_over_remaining_minutes(self):
        self.record["spent"]["minutes"] = 10
        self.invalid("budget")

    def test_budget_exhaustion_allows_handoff(self):
        self.record["spent"]["minutes"] = 31
        self.record["decision"] = "handoff"
        self.record["next"] = None
        self.valid()

    def test_same_failed_hypothesis_stops(self):
        self.record["history"] = [{"hypothesis_id": "H-rescue-tradeoff", "outcome": "not_improved", "build": self.record["build"], "evidence": ["E1"], "note": "no effect"}] * 2
        self.invalid("stagnation")

    def test_new_hypothesis_after_failure_allowed(self):
        self.record["history"] = [{"hypothesis_id": "old-hypothesis", "outcome": "not_improved", "build": self.record["build"], "evidence": ["E1"], "note": "no effect"}] * 2
        self.valid()

    def test_alternating_failed_hypotheses_cannot_bypass_stagnation(self):
        self.record["history"] = [{"hypothesis_id": h, "outcome": "not_improved", "build": self.record["build"], "evidence": ["E1"], "note": "no effect"} for h in ["H-rescue-tradeoff", "other", "H-rescue-tradeoff", "other"]]
        self.invalid("stagnation")

    def test_zero_minute_work_not_allowed_at_exhausted_budget(self):
        self.record["spent"]["minutes"] = 30
        self.record["next"]["minutes"] = 0
        self.invalid("budget")

    def test_oversized_number_rejected_cleanly(self):
        self.record["limits"]["minutes"] = 10 ** 400
        code, output = self.check()
        self.assertNotEqual(code, 0)
        self.assertTrue(output["errors"])

    def test_cost_and_history_cannot_be_reset_silently(self):
        previous = copy.deepcopy(self.record)
        previous["spent"]["iterations"] = 1
        self.invalid("spent", previous=previous)

    def test_bad_references_rejected(self):
        self.record["next"]["addresses"] = ["missing"]
        self.invalid("unknown")

    def test_malformed_json_is_clean_failure(self):
        self.invalid("JSON", raw="{")

    def test_bad_types_are_clean_failures(self):
        for field in ["evidence", "assessments", "findings", "history"]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.record)
                bad[field] = 7
                self.invalid(field, record=bad)

    def test_nested_bad_types_are_clean_failures(self):
        for container, key in [("evidence", "kind"), ("evidence", "scopes"), ("assessments", "aspect"), ("findings", "severity")]:
            with self.subTest(container=container, key=key):
                bad = copy.deepcopy(self.record)
                bad[container][0][key] = {"invalid": True}
                code, output = self.check(record=bad)
                self.assertNotEqual(code, 0)
                self.assertTrue(output["errors"])

    def test_duplicate_json_keys_rejected(self):
        self.invalid("duplicate JSON", raw='{"decision":"promote","decision":"stop"}')

    def test_nonfinite_json_numbers_rejected(self):
        self.invalid("JSON", raw='{"version":NaN}')


if __name__ == "__main__":
    unittest.main()
