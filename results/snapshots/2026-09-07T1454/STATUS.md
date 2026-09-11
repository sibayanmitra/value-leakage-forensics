# Snapshot 2026-09-07T14:54 +0530

Frozen copy of every result file the `run_backstop.sh` run has produced so far,
taken while stage 2 (steering) was still in flight. Nothing here is re-generated;
`steer_dm.jsonl` is a **partial** file — see below.

## Backstop stage state at snapshot time

| stage | job | rows | status |
|---|---|---|---|
| 0 | below_ours / valence_above / valence_below (2x2) | 60 / 60 / 60 | complete 03:54 |
| 1 | warned_anchor (GPU2) | 60 | complete 05:19 |
| 1 | warned_values (GPU3) | 60 | complete 05:33 |
| 2 | steer_dm (GPU0) | 252 / 324 | **RUNNING** — random-control arm, 0/72 |
| 3 | disclose_naked_number / _above_good / _baseline | 0 | not started |

steer_dm arms complete: anchor+ -> baseline (a=0,6,12); valence- -> above_good (a=6,12);
valence+ -> neutral_T (a=6,12). Remaining: random -> above_good (a=6,12), the negative control.

## Files (rows, bytes, sha256)

| file | rows | bytes | sha256 (first 16) |
|---|---|---|---|
| above_ours3.jsonl | 60 | 2045134 | `cf339c06525e1d52` |
| backstop.log | 8 | 272 | `35ed89f1ebee244a` |
| below_ours.jsonl | 60 | 2035866 | `5f50eafef4fbaa00` |
| ladder_matched.json | 265 | 2906 | `10bebf83e58b03fa` |
| naked_number.jsonl | 60 | 1328678 | `51cb54a09dec234a` |
| neutral_ours3.jsonl | 60 | 2037125 | `c9760ab8b09f5c2f` |
| our_baseline.jsonl | 100 | 2695985 | `6a4cad2437081255` |
| probe_controlled.csv | 37 | 5713 | `644e7963175979b3` |
| probe_results.csv | 45 | 1626 | `821be82fbcc17e7a` |
| steer_dm.jsonl | 252 | 18972967 | `f8e8d868edfff017` |
| steer_dm.log | 32 | 7911 | `d251c5f9cf17ca93` |
| valence_above.jsonl | 60 | 1695410 | `8b7f0b147777ad23` |
| valence_below.jsonl | 60 | 1736477 | `9e82fb8ae2df89d3` |
| warned_anchor.jsonl | 60 | 2017216 | `36e6d13a3d464634` |
| warned_anchor.log | 9 | 6360 | `e3fbd69c84327d0c` |
| warned_values.jsonl | 60 | 2148999 | `d06969993aafbb74` |
| warned_values.log | 9 | 6578 | `9592988b4af35d57` |

## Not snapshotted (deliberately)

- `probe_full_X.npy` (2.0 GB) and `probe_results_X.npy` (993 MB) — activation matrices, too large; unchanged since Sep 6.
- Authors' rollouts and all pre-Sep-7 experiment outputs — already stable in `results/`.

## Known-dead jobs at snapshot time

- `gate38_a.jsonl` / `gate38_b.jsonl`: 0 rows, logs stop mid model-load Sep 6 22:51, no traceback.
- `probe_full.csv`: never written; `logs/probe_full.log` stops after "layer 8 done" (of 11) at Sep 6 23:11.
  Activations (`probe_full_X.npy`, `probe_full_meta.jsonl`) were written and are intact.
