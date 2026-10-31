# Faultless Domino Tilings

A backtracking solver that searches for *faultless* tilings of a rectangular
grid: coverings by 2x1 dominoes in which every internal grid line is crossed by
at least one domino.

Grew out of a first-year group research project at UCL exploring domino tilings
and fault lines.

## The problem

Tile an m x n grid completely with dominoes, each covering two adjacent cells.

A **fault line** is an internal horizontal or vertical line that runs the full
width or height of the grid without cutting through any domino. A tiling with no
such line is called faultless, and it is a much stronger condition than simply
being a valid tiling. Most tilings have fault lines. On a 6x6 board, for
instance, none of the valid tilings are faultless at all.

The solver answers, for a given grid, whether a faultless tiling exists, and
returns one if it does.

## How it works

A naive search enumerates every tiling and filters for the faultless ones, which
is hopeless past small boards since the number of tilings grows exponentially.
This implementation does two things to avoid that.

### Bitmask board state

The board is not a 2D array. Occupancy is a single Python integer, one bit per
cell, so a 10x10 board is a 100-bit number. Placing a domino is a bitwise OR, and
checking whether two cells are free is one AND:

```python
if (occupied & domino_mask) == 0:
```

Which internal lines have already been crossed is tracked the same way, as two
more integers: one bit per horizontal gap, one per vertical gap.

### Pruning on unreachable fault lines

This is what makes the search tractable. After each placement, the solver asks,
for every line not yet crossed, whether *any* domino could still cross it. If a
line is uncrossed and no legal domino remains that would cross it, the branch can
never produce a faultless tiling, so it is abandoned immediately rather than
explored to completion.

```python
def line_can_still_be_crossed(occupied, possible_domino_masks):
    return any((occupied & m) == 0 for m in possible_domino_masks)
```

The search also always fills the lowest-indexed empty cell rather than an
arbitrary one, which forces a canonical ordering and stops the same partial
tiling being reached by different routes.

Boards with an odd number of cells return immediately, since a domino always
covers two.

## Instrumentation

The solver returns a stats dictionary alongside its results:

| | |
|---|---|
| `complete_tilings_checked` | full coverings reached |
| `branches_pruned_by_fault_line` | partial tilings abandoned early |
| `faultless_tilings_found` | solutions meeting the crossing condition |

The ratio between the first two shows how much work the pruning rule is actually
saving.

## Visualisation

Results are drawn with networkx and matplotlib. The grid becomes a
`grid_2d_graph`, cells are drawn as nodes, and the chosen tiling is overlaid as a
set of highlighted edges, so a domino is literally an edge in a perfect matching
of the grid graph.

## Files

```
aaa_optimized.py                The solver, pruning rule and visualisation
drawing 6x6 explanation.py      Scratch script for grid layout experiments
python_explanation.md           Line-by-line walkthrough of the solver
```

Grid size and search behaviour are set by constants at the top of
`aaa_optimized.py`: `ROWS`, `COLS`, `STOP_AFTER_FIRST`, `PRUNE_EARLY` and
`SHOW_FIRST`.

`drawing 6x6 explanation.py` is a working file kept for reference rather than a
finished component. Its pair-drawing loop is currently a no-op.
