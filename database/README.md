# Miles-Guo_public_archive Database

The official SQLite build artifact is:

```text
database/Miles-Guo_public_archive.sqlite3
```

It is a rebuildable query product, not the sole source of truth.

The intended contract is:

```bash
rm -f database/Miles-Guo_public_archive.sqlite3
python scripts/build_db.py
python scripts/validate_db.py
```

with the database recreated from Git-tracked `data/` plus `schema/`.

Do not create alternative official database names. Large media, cache and model files do not belong here.
