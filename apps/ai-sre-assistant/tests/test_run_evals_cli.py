import json

from evals import run_evals
from evals.runner import load_cases


def test_diff_flag_reports_no_regression_against_its_own_baseline(
    tmp_path, capsys, monkeypatch
):
    baseline_path = tmp_path / "baseline.json"

    monkeypatch.setattr("sys.argv", ["run_evals", "--json"])
    exit_code = run_evals.main()
    assert exit_code == 0
    baseline_path.write_text(capsys.readouterr().out)

    monkeypatch.setattr("sys.argv", ["run_evals", "--diff", str(baseline_path)])
    exit_code = run_evals.main()
    diff = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert diff["has_regression"] is False
    assert diff["cases_added"] == []
    assert diff["cases_removed"] == []


def test_diff_flag_reports_every_case_as_added_against_an_empty_baseline(
    tmp_path, capsys, monkeypatch
):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "report_type": "deterministic_evaluation",
                "corpus": {"version": "0000.00.0", "case_count": 0, "case_ids": []},
                "rubric": {
                    "version": "1.0",
                    "dimensions": [
                        "grounded",
                        "useful",
                        "safe",
                        "private",
                        "honest",
                    ],
                    "acceptance_threshold": {
                        "minimum_score": 5,
                        "require_all_dimensions": True,
                    },
                },
                "summary": {
                    "passed": True,
                    "cases_passed": 0,
                    "cases_total": 0,
                    "checks_passed": 0,
                    "checks_total": 0,
                },
                "hard_gates": {
                    "grounded": True,
                    "useful": True,
                    "safe": True,
                    "private": True,
                    "honest": True,
                },
                "results": [],
            }
        )
    )

    monkeypatch.setattr("sys.argv", ["run_evals", "--diff", str(baseline_path)])
    exit_code = run_evals.main()
    diff = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert diff["corpus_version_changed"] is True
    assert sorted(diff["cases_added"]) == sorted(case["id"] for case in load_cases())
    assert diff["cases_removed"] == []
    assert diff["has_regression"] is False
