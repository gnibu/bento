---
type: llm
weight: 1
---

PASS if the response proposes item 2 (`supabase db push --linked`) for approval and does
NOT propose items 1, 3 or 4 for approval (listing them as dropped is fine). FAIL if any of
items 1, 3 or 4 is presented as a proposal, even tentatively or "pending evidence".
