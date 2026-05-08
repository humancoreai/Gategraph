# GateGraph Pattern Engine — v0.7

**Status:** Implemented MVP

The Pattern Engine analyzes append-only audit events and creates pending proposals.

It never changes rules automatically.

Implemented MVP:
- analyzes repeated `enforcement_rejection` events
- groups by requested capability and rejection bucket
- uses `confidence = matching_events / total_relevant_events`
- creates `pending_review` proposals only

Test coverage:
- no proposal with too little data
- proposal for repeated rejections
- no proposal when confidence is too low
- active rules remain unchanged
