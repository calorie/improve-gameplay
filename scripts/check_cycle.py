"""Validate an improvement record and its next action; never score a game's fun.

Python standard library only. Read-only, no game execution, network or purchases.
Exit 0 means the declared record passes checks, not that its claims are true.
"""
import argparse
import json
import math
from pathlib import Path

SCOPES = {"moment", "sequence", "whole"}
ASPECTS = {"enjoyment", "comprehension", "coherence", "expression", "function"}
KINDS = {"runtime", "human", "static", "design", "simulation"}
RANK = {"core": 0, "major": 1, "minor": 2}


def validate(record, previous=None):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def member(value, options):
        return isinstance(value, str) and value in options

    def number(value):
        return type(value) in (int, float) and 0 <= value <= 2**53 - 1 and (type(value) is int or math.isfinite(value))

    def strings(value, nonempty=False):
        return isinstance(value, list) and all(text(v) for v in value) and (bool(value) or not nonempty)

    if not isinstance(record, dict):
        return ["record must be an object"]
    r = record
    require(type(r.get("version")) is int and r["version"] == 1, "version must be 1")
    for key in ("build", "boundary"):
        require(text(r.get(key)), f"{key} must be nonempty text")
    contract = r.get("contract")
    require(isinstance(contract, dict), "contract must be an object")
    if isinstance(contract, dict):
        for key in ("project", "audience"):
            require(text(contract.get(key)), f"contract.{key} is required")
        for key in ("goals", "quality_floor", "intentional_ambiguity"):
            require(strings(contract.get(key), key != "intentional_ambiguity"), f"contract.{key} must be a text list")
    for key, fields in (("limits", ("minutes", "iterations", "stall")), ("spent", ("minutes", "iterations"))):
        obj = r.get(key)
        require(isinstance(obj, dict), f"{key} must be an object")
        if isinstance(obj, dict):
            for field in fields:
                value = obj.get(field)
                require(number(value), f"{key}.{field} must be a finite nonnegative number")
                if field != "minutes":
                    require(type(value) is int, f"{key}.{field} must be an integer")
                if key == "limits":
                    require(number(value) and value > 0, f"limits.{field} must be positive")
    for key in ("evidence", "assessments", "findings", "history"):
        require(isinstance(r.get(key), list) and all(isinstance(v, dict) for v in r.get(key, []) if isinstance(r.get(key), list)), f"{key} must be a list of objects")
    require(r.get("decision") in ("iterate", "keep_provisional", "promote", "handoff", "stop"), "unknown decision")
    if errors:
        return errors

    evidence = {}
    for item in r["evidence"]:
        for key in ("id", "build", "source", "observation"):
            require(text(item.get(key)), f"evidence.{key} is required")
        require(member(item.get("kind"), KINDS), "unknown evidence.kind")
        require(strings(item.get("scopes"), True) and set(item.get("scopes", [])) <= SCOPES, "evidence.scopes invalid")
        if text(item.get("id")):
            require(item["id"] not in evidence, "duplicate evidence id")
            evidence[item["id"]] = item
    if errors:
        return errors

    def refs(obj, label):
        ids = obj.get("evidence")
        require(strings(ids), f"{label}.evidence must be a list of ids")
        if not strings(ids):
            return []
        require(all(i in evidence for i in ids), f"{label}: unknown evidence id")
        return [evidence[i] for i in ids if i in evidence]

    assessed = set()
    for a in r["assessments"]:
        require(member(a.get("aspect"), ASPECTS), "unknown assessment aspect")
        require(member(a.get("scope"), SCOPES), "unknown assessment scope")
        require(a.get("status") in ("pass", "fail", "unknown", "na"), "unknown assessment status")
        require(text(a.get("claim")), "assessment.claim is required")
        if not isinstance(a.get("aspect"), str) or not isinstance(a.get("scope"), str):
            continue
        pair = (a["aspect"], a["scope"])
        require(pair not in assessed, "duplicate assessment aspect/scope")
        assessed.add(pair)
        linked = refs(a, "assessment")
        if a.get("status") in ("pass", "fail"):
            current = [e for e in linked if e.get("build") == r["build"] and a["scope"] in e.get("scopes", [])]
            require(bool(current), "pass/fail requires current evidence matching scope")
            if a["aspect"] in ("enjoyment", "comprehension"):
                require(any(e.get("kind") == "human" for e in current), "enjoyment/comprehension pass/fail requires current human evidence at scope")
            else:
                require(any(e.get("kind") in ("runtime", "human") for e in current), "pass/fail requires current execution evidence, not static/design/simulation")
        if a.get("status") == "fail":
            require(bool(linked), "failed assessment requires evidence; otherwise use unknown")
        if a.get("aspect") == "enjoyment":
            require(a.get("status") != "na", "enjoyment cannot be na")
    for scope in SCOPES:
        require(("enjoyment", scope) in assessed, f"enjoyment assessment missing at {scope}")
    require(("coherence", "whole") in assessed, "whole coherence assessment missing")
    for aspect in ASPECTS:
        require(any(pair[0] == aspect for pair in assessed), f"missing assessment aspect {aspect}")

    findings = {}
    for f in r["findings"]:
        for key in ("id", "observation", "hypothesis"):
            require(text(f.get(key)), f"finding.{key} is required")
        require(member(f.get("severity"), RANK), "unknown finding severity")
        require(f.get("status") in ("open", "resolved"), "unknown finding status")
        require(member(f.get("aspect"), ASPECTS), "unknown finding aspect")
        linked = refs(f, "finding")
        if f.get("status") == "resolved":
            require(text(f.get("resolved_build")), "resolved finding requires resolved_build")
            require(any(e.get("build") == f.get("resolved_build") and e.get("kind") in ("runtime", "human") for e in linked), "resolved finding requires execution evidence at resolved_build")
        if text(f.get("id")):
            require(f["id"] not in findings, "duplicate finding id")
            findings[f["id"]] = f
    for h in r["history"]:
        for key in ("hypothesis_id", "build", "note"):
            require(text(h.get(key)), f"history.{key} is required")
        require(h.get("outcome") in ("improved", "not_improved", "unknown"), "unknown history outcome")
        linked = refs(h, "history")
        if h.get("outcome") != "unknown":
            require(any(e.get("build") == h.get("build") and e.get("kind") in ("runtime", "human") for e in linked), "history outcome requires execution evidence at recorded build")
    if errors:
        return errors

    action = r.get("next")
    terminal = r["decision"] in ("stop", "handoff", "promote")
    if terminal:
        require(action is None, "terminal decision requires next=null")
    else:
        require(isinstance(action, dict), "next action is required")
        if isinstance(action, dict):
            require(action.get("kind") in ("experiment", "collect", "polish"), "unknown next.kind")
            for key in ("hypothesis_id", "change", "check_function", "check_fun", "check_regression"):
                require(text(action.get(key)), f"next.{key} is required")
            require(strings(action.get("addresses")), "next.addresses must be a list of finding ids")
            require(number(action.get("minutes")) and action["minutes"] > 0, "budget: next.minutes must be finite and positive")
            if strings(action.get("addresses")):
                require(all(i in findings for i in action["addresses"]), "next addresses unknown finding")
                opened = [f for f in findings.values() if f["status"] == "open"]
                if opened:
                    priority = min(RANK[f["severity"]] for f in opened)
                    require(any(f["id"] in action["addresses"] and RANK[f["severity"]] == priority for f in opened), "priority: address a highest-severity open finding")
                    if priority < 2:
                        require(action.get("kind") != "polish", "priority: unrelated polish blocked by core/major findings")
            if number(action.get("minutes")):
                require(r["spent"]["minutes"] + action["minutes"] <= r["limits"]["minutes"], "budget: next work exceeds remaining minutes")
            require(r["spent"]["minutes"] < r["limits"]["minutes"], "budget: time limit reached")
            require(r["spent"]["iterations"] < r["limits"]["iterations"], "budget: iteration limit reached")
            attempts = [h for h in r["history"] if h["hypothesis_id"] == action.get("hypothesis_id")]
            recent = attempts[-r["limits"]["stall"]:]
            stalled = len(recent) == r["limits"]["stall"] and all(h["outcome"] != "improved" for h in recent)
            require(not stalled, "stagnation: change hypothesis or hand off; do not repeat unchanged")

    comparison = r.get("comparison")
    if comparison is not None:
        require(isinstance(comparison, dict), "comparison must be object or null")
        if isinstance(comparison, dict):
            for key in ("baseline", "candidate", "tradeoffs", "conditions"):
                require(text(comparison.get(key)), f"comparison.{key} is required")
            require(comparison.get("candidate") == r["build"], "comparison candidate must be current build")
            require(comparison.get("baseline") != comparison.get("candidate"), "comparison baseline must differ from candidate")
            require(comparison.get("verdict") in ("better", "worse", "mixed", "unknown"), "unknown comparison verdict")
            linked = refs(comparison, "comparison")
            for field in ("baseline", "candidate"):
                require(any(e.get("build") == comparison.get(field) and e.get("kind") in ("runtime", "human") for e in linked), f"comparison needs {field} execution evidence")
    if r["decision"] == "promote":
        require(all(a["status"] in ("pass", "na") for a in r["assessments"]), "promotion blocked by failed or unknown assessments")
        require(not any(f["status"] == "open" and f["severity"] != "minor" for f in findings.values()), "promotion blocked by core/major findings")
        if isinstance(comparison, dict):
            require(comparison.get("verdict") in ("better", "mixed"), "promotion comparison does not support adoption")
    if r["decision"] == "keep_provisional":
        require(any(e["build"] == r["build"] and e["kind"] == "runtime" for e in evidence.values()), "provisional adoption requires current runtime evidence")

    if previous is not None:
        prior_errors = validate(previous)
        if prior_errors:
            errors.extend("previous: " + e for e in prior_errors)
        else:
            require(r["contract"] == previous["contract"], "contract changed: authorize a separate design decision and baseline")
            require(r["boundary"] == previous["boundary"], "boundary changed: cannot silently narrow acceptance scope")
            require(r["limits"] == previous["limits"], "budget limits changed without a new work allocation")
            for key in ("minutes", "iterations"):
                if key in previous["spent"]:
                    require(r["spent"][key] >= previous["spent"][key], "spent counters must not decrease")
            require(r["history"][:len(previous["history"])] == previous["history"], "history must retain prior outcomes")
            for old in previous["evidence"]:
                require(evidence.get(old["id"]) == old, "prior evidence must be retained unchanged")
            for old in previous["findings"]:
                new = findings.get(old["id"])
                require(new is not None, "prior finding cannot disappear; resolve with evidence")
                if new is not None:
                    require(all(new[key] == old[key] for key in ("aspect", "observation")), "finding identity changed: retain original aspect and observation")
                    if old["status"] == new["status"] == "resolved":
                        require(new["resolved_build"] == old["resolved_build"], "historical resolved_build cannot silently change")
                if new is not None and old["status"] == "open" and new["status"] == "open":
                    require(RANK[new["severity"]] <= RANK[old["severity"]], "open finding severity cannot silently decrease")
            old_findings = {f["id"]: f for f in previous["findings"]}
            for f in findings.values():
                old = old_findings.get(f["id"])
                if f["status"] == "resolved" and (old is None or old["status"] != "resolved"):
                    require(f["resolved_build"] == r["build"], "new resolution requires current build evidence")
    return errors


def load(path):
    def reject_constant(value):
        raise ValueError("nonfinite JSON number: " + value)
    def unique_keys(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate JSON key: " + key)
            obj[key] = value
        return obj
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant, object_pairs_hook=unique_keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record")
    parser.add_argument("--previous", help="Prior immutable accepted record for continuity checks")
    args = parser.parse_args()
    try:
        record = load(args.record)
        previous = load(args.previous) if args.previous else None
        errors = validate(record, previous)
    except (OSError, ValueError, UnicodeError) as error:
        record, errors = {}, ["JSON/input error: " + str(error)]
    result = {"record_valid": not errors, "decision": record.get("decision") if isinstance(record, dict) else None,
              "errors": errors, "notice": "Checks declared evidence and workflow only. Does not verify sources, judge enjoyment, execute tasks, or authorize changes."}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
