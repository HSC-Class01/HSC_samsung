# Workflow validation

- `github_workflows/monthly_update.yml`: YAML parsed successfully.
- `github_workflows/pages_deploy.yml`: YAML parsed successfully.
- Python source syntax: parsed successfully.
- The package intentionally contains no hidden files or directories.
- The workflow files are stored under `github_workflows/` in the zip so the zip itself contains no `.github` hidden directory. Copy them to `.github/workflows/` after extraction.

## Schedule

`0 21 1 * *` = 21:00 UTC on the 1st day of each month = 06:00 KST on the 1st day of each month.

## Required repository secret

`DART_API_KEY`
