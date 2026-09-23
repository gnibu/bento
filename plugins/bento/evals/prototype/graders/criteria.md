---
type: llm
weight: 1
---

Score how well the response applies **prototype / throwaway-spike** discipline. A strong
answer covers most of:

- **Build throwaway, fast** — a scratch build separate from production, lightest stack, no
  tests/abstractions/framework; speed over polish.
- **Compare variants side by side** — build the alternatives behind one switcher, each
  labeled.
- **Verify by observation** — screenshot/observe each variant rather than asserting; present
  tradeoffs + a recommendation, and treat the code as throwaway (real build follows).

Full credit: throwaway-scratch + variants-compared + decide-by-observation all present.
Partial: "just try some options" without the throwaway/scratch discipline. Low: proposes
building it properly / production-quality to decide.
