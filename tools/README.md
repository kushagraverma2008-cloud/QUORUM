# QUORUM Build-Time Data Ingestion Tools

This directory contains one-off build and data processing scripts used to extract, curate, and normalize expert mental models into `data/expert_council_catalog.json`.

These tools are **build-time only** and are not required to run the production QUORUM application.

## Tool Inventory

- `harvest_all_experts.py`: Parses the structured expert roster from raw datasets into intermediate JSON schema.
- `harvest_youtube_links.py` / `batch_extract_transcripts.py`: Ingestion pipeline for extracting video transcripts of interviews and lectures.
- `distill_knowledge.py` / `batch_distill_all.py`: Distills principles, signature warnings, and contrarian perspectives into standardized `ExpertProfile` schemas.
- `scan_secrets.py`: Static analysis utility ensuring zero credentials or API keys exist in git-tracked code.
- `generate_sample_reports.py`: Pre-generates reference council evaluations for documentation and offline demos.

## Dependencies

Tools in this folder use dependencies listed in `tools/requirements.txt` (e.g. `openpyxl`, `youtube-transcript-api`).
