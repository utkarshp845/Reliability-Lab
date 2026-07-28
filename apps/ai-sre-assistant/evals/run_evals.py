import argparse
import json

from evals.runner import (
    RUBRIC_DIMENSIONS,
    run_comparison_suite,
    run_provider_suite,
    run_suite,
    run_versioned_suite,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI SRE Assistant evaluations.")
    report_group = parser.add_mutually_exclusive_group()
    report_group.add_argument(
        "--provider-report",
        action="store_true",
        help="Run the corpus with optional provider enrichment and print a bounded JSON cost report.",
    )
    report_group.add_argument(
        "--comparison-report",
        action="store_true",
        help="Compare deterministic evaluation with an optional provider path and print a bounded JSON summary.",
    )
    report_group.add_argument(
        "--json",
        action="store_true",
        help="Run deterministic evaluation and print the versioned machine-readable report.",
    )
    args = parser.parse_args()

    if args.provider_report:
        suite = run_provider_suite()
        print(json.dumps(suite, indent=2, sort_keys=True))
        return 0 if suite["passed"] else 1

    if args.comparison_report:
        report = run_comparison_suite()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["deterministic"]["passed"] else 1

    if args.json:
        report = run_versioned_suite()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["summary"]["passed"] else 1

    suite = run_suite()
    print("AI SRE Assistant evaluation")
    print("=" * 35)
    for result in suite["results"]:
        checks = " ".join(
            f"{dimension}={'pass' if result['rubric'][dimension] else 'fail'}"
            for dimension in RUBRIC_DIMENSIONS
        )
        print(f"{result['id']}: {result['score']}/{result['max_score']} {checks}")

    print(
        f"\n{suite['cases_passed']}/{suite['cases_total']} cases passed; "
        f"{suite['checks_passed']}/{suite['checks_total']} rubric checks passed."
    )
    return 0 if suite["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
