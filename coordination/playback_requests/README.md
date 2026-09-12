# Playback Requests

Worker-writable business coordination area for an **active claimed** `P9-PLAYBACK-*` task.

One request per canonical timed segment:

```text
coordination/playback_requests/<CASE_ID>/<SEGMENT_ID>.json
```

Required contract: `playback-request-v1`. See `docs/MEDIA_AUDIT.md` and `START_HERE.md`.

The request owner must equal the active claim owner. `media_url` must already exist in repository source provenance for the same canonical live. Invalid/unclaimed/arbitrary-URL requests are rejected by the service.

Do not put videos, audio, screenshots, model files or caches here.
