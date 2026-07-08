# mini-nucleiq

Analyze breast-tissue samples for simplified marker patterns. Given a **sample name** and **one or
more algorithms**, `mini-nucleiq` fetches the sample's cells (an array of `0`/`1`) from the external
**Samples API**, runs each algorithm (producing positive-cell counts and a positivity percentage),
and aggregates a final **POSITIVE / NEGATIVE** result.

The original challenge brief is preserved verbatim in [`TASK.md`](TASK.md).

## Algorithms

Each algorithm scans the cell array (indexes start at `0`) and counts *positive cells*; it is
positive when the positivity exceeds its threshold.

| Algorithm         | A cell is positive when…                               | Threshold |
| ----------------- | ------------------------------------------------------ | --------- |
| `even-zeroes`     | it is a `0` at an even index                           | `> 30%`   |
| `contiguous-ones` | it is a `1` whose previous cell is also `1`            | `> 20%`   |
| `surrounded-ones` | it is a `1` whose previous and next cells are both `0` | `> 10%`   |

The **final result** is `POSITIVE` when **more than half** of the selected algorithms are positive,
otherwise `NEGATIVE`.