---
max_turns: 6
allowed_tools: [Skill]
---

Plan this before I code it: checkout gets a `discount_code` field across three repositories.
- `api`: a migration adding the `discount_code` column, the model field and its validation,
  the checkout endpoint accepting it, and the API docs.
- `web`: the input on the checkout form, and sending it to the endpoint.
- `mobile`: the same input and request in the app.
Web and mobile can't ship before the API change is deployed. Give me the PR checklist.
