# Server DB Boundary

Release: `v0.17.9_CANDIDATE`
Base: `v0.17.8_STABLE`
Status: candidate

The minimal local HTTP adapter remains a single-node adapter.

`/evaluate`, `/status`, and `/monitoring` use the same server-side DB boundary lock. This avoids mixed read/write access across local ThreadingHTTPServer worker threads without introducing a connection pool, async rewrite, PostgreSQL, or multi-node behavior.

This is not an enterprise concurrency claim.
