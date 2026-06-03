"""Data ingestion test harness package.

Three-level verification over the OpenNEM / BOM / Solcast ingestion pipelines:
  Level 1 — fetcher contract tests (offline, against recorded JSON fixtures)
  Level 2 — pipeline integration + data-quality assertions (citylab_test)
  Level 3 — agent API + CLI smoke tests
"""
