# Miles-Guo_public_archive

## Mandatory reading before work

Every agent working in this repository MUST read this file and the following documents before planning, editing, collecting data, or committing:

1. `docs/PROJECT_REQUIREMENTS.md` — complete user requirements, source analysis, schema, Pilot coverage, quality gates, and acceptance queries.
2. `docs/NAMING_AND_WORKFLOW.md` — authoritative naming rules, repository boundaries, and working procedure.
3. `README.md` and any existing relevant `docs/`, `schema/`, `reports/`, and `tests/` files.

Do not rely on a previous chat, a cached summary, or another agent's recollection instead of reading these files. This requirement applies to primary agents and delegated agents. A delegating agent must pass on these requirements. If the required files are unavailable, stop dependent changes and report the missing file; do not invent requirements.

## Scope and precedence

- Only modify `witnessGIT/Miles-Guo_public_archive`. Default branch: `main`.
- Never modify `witnessGIT/movie_production` or any other repository for this task.
- Official project name: `Miles-Guo_public_archive`.
- Only official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Current explicit user instructions take precedence. Among the saved requirements, the later naming rules override older examples, especially the six-digit segment suffix.
- Archive First, Application Second. This is a searchable public digital archive, not a video production project.

## Required work discipline

- Inspect remote URL, branch, main history, existing files, working tree, and applicable instructions before changes. Preserve unrelated or uncommitted work.
- Analyze the three public source sites before collection. Limit Pilot to 20–30 real livestreams across years, including all required coverage cases.
- One livestream has one internal live ID and multiple source records. Preserve curated text and ASR separately, with complete provenance.
- Use seconds as the primary locator. Never invent timestamps, FPS, matches, source availability, or verification results.
- Keep JSON/JSONL under `data/` as the Git source of truth. Rebuild SQLite and FTS5 entirely from `data/` and `schema/`.
- Randomly audit at least 60 segments. Actual playback checks are required for time accuracy; checking that a URL contains a timestamp is insufficient. Mark unperformed checks as unverified.
- Do not recommend full collection unless evidence meets the user's quality gates. Stop expansion after Pilot and report the result.
- Only access normally public content, at low concurrency with request spacing and caching. Do not bypass login, CAPTCHA, paywalls, access controls, or DRM.
- Never commit full video, large audio, models, or cache. Remove temporary downloaded media after analysis.
- Make clear stage-based commits. Run checks appropriate to each stage; report actual results and unresolved failures.
- Distinguish SITE_ANALYSIS, PILOT, FULL_ARCHIVE, and MAINTENANCE. Do not describe partial work as completed.
- Update these saved requirements when the user changes project policy so later agents have the current contract.
