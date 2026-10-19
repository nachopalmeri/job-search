# Plan: auditable source coverage details

## Goal and decisions

Make daily source records distinguish a source that was opened from its configured query/page families actually being covered. Preserve older reports and user-generated radar artifacts. A source with `attempted < total` is incomplete and must keep `--check` non-zero; unknown totals remain explicitly unknown in the note rather than being guessed.

## Paths

- `tests/test_source_coverage.py`
- `scripts/source_coverage.py`
- `AGENTS.md`
- `scripts/search_sources.json` and `scripts/buscar_portales.py` only if the review identifies a narrowly verifiable source URL/method correction.

## Dependency order

1. Add regression tests for partial query-family coverage and check output.
2. Add optional attempted/total evidence to the coverage CLI and preserve old report entries.
3. Clarify the daily runbook: counts are signals, not individually verified vacancies; record query/page coverage; distinguish discovery from listing-level verification.
4. Run focused and full tests plus daily coverage check; review the diff and keep daily generated artifacts out of the commit.

## Acceptance and stop conditions

- `attempted < total` cannot be recorded as complete and is reported as partial by `--check`.
- Existing report format remains readable and `--init` preserves prior entries.
- Tests: `python -m unittest tests.test_source_coverage -v`; full suite: `python -m pytest -q` if pytest is installed; syntax: `python -m compileall -q scripts`.
- Do not claim a full search while any required source is partial/blocked. Merge only after explicit user approval; Nacho explicitly authorized integration and push for this change on 2026-10-19.
