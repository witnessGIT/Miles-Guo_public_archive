# Pilot Report

## Scope

Initial Pilot validates the archive model against three consecutive public Miles Guo video records:

- 2023-03-12 (`LIVE_20230312_001`)
- 2023-03-13 (`LIVE_20230313_001`)
- 2023-03-14 (`LIVE_20230314_001`)

Sources checked: GWINS and GHOT. GETTR Search remains a discovery source pending a reproducible per-item interface.

## Result

The one-live/many-sources model is necessary and works for the observed records.

The strongest conflict found is the 2023-03-12 item:

- GWINS own identifier: `20230312_1`
- GHOT visible label: `2023.03.12-1`
- GHOT route id: `2023-03-12-3`

The canonical record therefore stays `LIVE_20230312_001`, while both source ids are retained unchanged.

## Source strengths

GWINS is useful for historical discovery, original GETTR/Rumble locators and manually organized text. GHOT is useful for technical metadata and automatic time-addressable transcription. These text types must remain separate because GHOT itself labels its transcript as automatic and error-prone.

## Next gate

The Pilot is considered structurally successful when:

1. lightweight GWINS inventory is collected;
2. SQLite is rebuilt from versioned data;
3. validation passes;
4. generated database path is exactly `database/Miles-Guo_public_archive.sqlite3`.

After that, enrichment should proceed in batches instead of attempting every historical detail page at once.
