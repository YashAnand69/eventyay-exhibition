# Exhibition #375: API regression recording

This is an actual recording of a live subprocess-output viewer, not a recording of the Checkin application UI. The current Checkin UI supplies both fields and is not the defect trigger. It executes Django's in-process HTTP test client through the production URL, session authentication and permissions, using isolated PostgreSQL/Redis test data. It does not claim an external network request or manual user QA.

- First: upstream dev `17d298337846c83c3e9cc2b14c04fdb200d895d6`: omitted-tags request loses the existing `vip` tag; one failure, three passing controls.
- Second: PR head `3cd2e6ea898bce0e12672c4b33105d2d97f7f8f7`: all four requests pass. Null retains tags, an explicit empty list clears them, and a supplied list replaces them.
- Production modules were checked byte-for-byte against those commits. Only the test was instrumented to print actual request payloads, response status, persisted state and expectations. App logging boilerplate is omitted from the viewer, not from the raw execution logs.
- Video: 27.52 seconds. See manifest for its SHA-256.

## Reproduce

Use the project's supported Python/Django/Eventyay environment, its matching migrations, an isolated PostgreSQL database and Redis. The test code is the same recorded HTTP regression with its existing event fixture included. From either source checkout, add the directory containing `demo_api_cases.py` to pytest discovery, and run:

```sh
PYTHONPATH=.:/path/to/matching/eventyay/app python -m pytest -p no:env --reuse-db /path/to/demo_api_cases.py -s -q --tb=short
```

Configure `DJANGO_SETTINGS_MODULE=eventyay.config.settings`, `EVY_RUNNING_ENVIRONMENT=testing`, the `EVY_POSTGRES_*` variables and `EVY_REDIS_URL` for local test services. Existing settings must enable the exhibition plugin. The exact local recording tooling is retained in the contribution ledger; no plugin production code or dependency was changed for this evidence.

Prepared with Codex assistance. No human-only authorship or personal QA certification is asserted.
