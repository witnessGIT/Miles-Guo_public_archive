# Current task: C2 candidate identity review

The C1 source-discovery phase is complete and sealed as history. Do not repeat C1 discovery and do
not use historical C1-only guides to stop current work.

Current work is `C2-REVIEW-*`: claim a fixed batch, then review candidates strictly one by one.

- Work mode claims 100 candidates, or all remaining candidates when fewer than 100 remain;
  ordinary chat mode claims exactly 20.
- Each candidate has its own claim, evidence artifact, final decision, and completion record.
- All claims in a batch must be published atomically: 100 for Work mode (or the complete final
  remainder when fewer than 100 remain) or exactly 20 for ordinary chat mode. An arbitrary partial
  batch fails CI.
- A candidate becomes `reviewed` only after a valid artifact exists under
  `data/current/candidate_reviews/` and the completion passes the validator.
- If evidence is insufficient, it is not complete. Leave it `in_progress`; after 10 hours it
  derives back to `unreviewed`.
- Do not perform playback review, download media, transcribe, segment, or do later video work.
- Do not read archived documentation or archived invalid records during normal work.

Work-mode entry:

```bash
git pull --ff-only
python scripts/agent_entry.py --mode auto
```

Before publishing candidate-review completion:

```bash
python scripts/validate_candidate_reviews.py
python -m unittest discover -s tests -p 'test_*.py' -v
```
