# SOURCE_POLICY

## Initial archive sources

Canonical `source_site` enum values for the initial phase:

- `gwins`
- `ghot`
- `gettrsearch`

Original-publication platforms are recorded separately (`gettr`, `rumble`, `youtube`, `twitter`, `x`, etc.).

## Source hierarchy

- `primary`: direct original-platform page/media locator when independently captured.
- `secondary`: archive/detail page that reproduces metadata, transcript or locators.
- `discovery`: list/search page used to discover an item before detail verification.

`is_primary` marks the preferred archive source row for reconstruction/query purposes; it does not claim that the archive site itself is the original publisher.

## Provenance requirements

Every imported source record keeps:

- source site;
- source URL;
- source-specific id when available;
- original platform and URL when explicitly observed;
- capture timestamp;
- source level;
- source-specific metadata/conflicts.

## Conflict handling

Never overwrite a conflicting source id to make sources appear consistent. Preserve both and document the discrepancy in `metadata_json` or a report.

## Availability handling

If a site is client-rendered, requires a session, or fails to expose a reproducible result interface, record the limitation and do not fabricate coverage. `gettrsearch` is currently handled this way in the Pilot.

## Media storage

Do not commit full livestream video/audio to Git. Store locators, metadata, transcript text and time positions. Temporary media belongs under ignored `cache/`.
