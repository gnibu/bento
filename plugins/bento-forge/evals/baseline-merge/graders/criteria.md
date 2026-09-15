---
type: llm
weight: 1
---

Evaluate whether the response preserves human ownership of generated L2 files.
The product contract is authoritative: the next baseline stores the **proposed
generated text**, while the working file stores the merged output. Do not replace
this contract with a different merge strategy. An answer that stores merged/current
hand-edited text in the next baseline MUST FAIL, even if its other advice is sound.
Full credit requires:

- Verify the recurring learning and the appropriate sink before proposing it.
- Build proposed text from the recorded generated baseline plus the learning,
  not by adopting current hand edits into the baseline.
- Preview with l2-state.py merge; explain current / baseline / proposed inputs
  and obtain approval of the merged diff before --apply.
- Save merged output in the target file and proposed generated text in the next
  baseline only after a successful merge.
- On conflict, leave both files and baseline unchanged, show the conflict, and
  seek a revised proposal/review. Unattended promotion skips it rather than
  forcing a merge. Never re-run init over the existing L2.

Partial credit for correct high-level merge advice missing operational details.
Low credit for direct overwrites, replacing the baseline with current hand edits,
automatically choosing one side of a conflict, or treating approval as implicit.
