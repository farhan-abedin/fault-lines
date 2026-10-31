# Python explanation: domino tiling solver and drawing script

This project is a pair of Python scripts that explore a classic domino-placement puzzle.

The main idea is:
- A grid is filled with dominoes.
- Each domino covers exactly 2 adjacent cells.
- We want to build a valid tiling.
- The special twist here is that the tiling must cross every internal fault line at least once, so it is not just any tiling—it is a “clean” or “faultless” tiling.

---

## 1) What the main script is doing

File: `aaa_optimized.py`

This file uses backtracking + pruning to search for valid tilings on a board.

### Key setup at the top

```python
import matplotlib.pyplot as plt
import networkx as nx

ROWS, COLS = 10, 10
STOP_AFTER_FIRST = True
PRUNE_EARLY = True
SHOW_FIRST = True
```

- `matplotlib.pyplot` is used to draw the final board.
- `networkx` is used to build a graph of the grid and draw nodes and edges.
- `ROWS` and `COLS` set the board size.
- `STOP_AFTER_FIRST = True` means the program stops as soon as it finds one valid tiling.
- `PRUNE_EARLY = True` means it abandons branches that are impossible to finish.
- `SHOW_FIRST = True` means it displays the first valid tiling we found.

---

## 2) The graph drawing helper

```python
def show_matching(rows, cols, matching):
    """show one valid tiling, nice and easy."""
    G = nx.grid_2d_graph(rows, cols)
    pos = {(i, j): (j, -i) for i, j in G.nodes()}

    plt.figure(figsize=(8, 8))
    nx.draw_networkx_nodes(G, pos, node_color="black", node_size=100)
    nx.draw_networkx_edges(G, pos, edgelist=matching, edge_color="red", width=3)
    plt.axis("off")
    plt.show()
```

This function:
- creates a 2D grid graph using `networkx`
- assigns each cell a position on screen
- draws all the cells as black dots
- highlights only the domino edges that are part of the matching
- draws the result in a red line overlay

So `matching` is a list of domino placements, like:

```python
((0, 0), (0, 1))
```

That means a domino placed horizontally between the two cells.

---

## 3) Bitmasks: the real trick in this code

This is the most important concept in the script.

The code does not store the board as a 2D array of booleans. Instead, it uses integer bitmasks.

### Why bitmasks?

Because Python integers can act like binary number strings. Each bit stands for one cell.

Example:
- cell 0 -> bit 0
- cell 1 -> bit 1
- cell 2 -> bit 2
- etc.

So a board with 10 x 10 = 100 cells uses a 100-bit number to represent occupancy.

### Example

```python
a = 0
b = 1
mask = (1 << a) | (1 << b)
```

This creates a number where bits 0 and 1 are set to 1.

If we say a domino covers cells 0 and 1, then:

```python
mask == 3
```

because binary `11` means “cells 0 and 1 are occupied.”

This lets the code check whether a domino is already used with a fast bit operation:

```python
if (occupied & domino_mask) == 0:
```

This means:
- `occupied` is the set of cells already covered
- `domino_mask` is the two cells for this domino
- `occupied & domino_mask` checks whether those cells overlap with anything already used
- if the result is 0, the cells are free

---

## 4) Creating all the crossing masks

```python
def make_crossing_masks(rows, cols):
    row_masks = [[] for _ in range(rows - 1)]
    col_masks = [[] for _ in range(cols - 1)]
```

This creates two lists:
- `row_masks[r]` stores all dominoes that can cross the horizontal gap between row `r` and `r + 1`
- `col_masks[c]` stores all dominoes that can cross the vertical gap between column `c` and `c + 1`

### Horizontal gap masks

```python
for r in range(rows - 1):
    for c in range(cols):
        a = r * cols + c
        b = (r + 1) * cols + c
        row_masks[r].append((1 << a) | (1 << b))
```

This loops through every position where a domino could cross a horizontal line between two rows.

If you imagine a board, there is a line between row 0 and row 1, row 1 and row 2, etc.

A domino crossing that line is vertical, because it goes from a cell above to a cell below.

So for each cell `(r, c)`, it creates a mask with:
- the cell above
- the cell below

This is stored for that gap index.

### Vertical gap masks

```python
for r in range(rows):
    for c in range(cols - 1):
        a = r * cols + c
        b = r * cols + (c + 1)
        col_masks[c].append((1 << a) | (1 << b))
```

This does the same thing for boundaries between columns.

A domino crossing a vertical interior line is horizontal.

So it stores the left and right cells for each possible crossing.

---

## 5) Checking whether a fault line is still possible

This is the heart of the “clean tiling” rule.

```python
def line_can_still_be_crossed(occupied, possible_domino_masks):
    return any((occupied & domino_mask) == 0 for domino_mask in possible_domino_masks)
```

This asks:
- “Is there still at least one domino that could cross this specific line?”

It checks all possible domino masks for that line and sees whether they are still open.

If at least one such domino has both cells unoccupied, this line can still be crossed.

---

## 6) The pruning rule: dead branches

```python
def fault_line_is_unavoidable(occupied, row_crossed_mask, col_crossed_mask, row_masks, col_masks):
    for r, possible_domino_masks in enumerate(row_masks):
        if not (row_crossed_mask & (1 << r)):
            if not line_can_still_be_crossed(occupied, possible_domino_masks):
                return True

    for c, possible_domino_masks in enumerate(col_masks):
        if not (col_crossed_mask & (1 << c)):
            if not line_can_still_be_crossed(occupied, possible_domino_masks):
                return True

    return False
```

This is what makes the algorithm smart.

### `row_crossed_mask`

This tracks which horizontal lines have already been crossed.

For example, if a domino crosses the line between rows 0 and 1, then bit 0 is set.

### `col_crossed_mask`

This tracks which vertical lines have already been crossed.

### Why this matters

A “faultless tiling” must cross every internal line at least once.

If a row or column gap is still un-crossed and no remaining domino can cross it, then the current partial tiling can never work. We can stop immediately.

This is huge because it prunes impossible branches before exploring them fully.

---

## 7) The main solver: `find_faultless_tilings`

```python
def find_faultless_tilings(rows, cols, stop_after_first=True, prune_early=True):
```

This function does the search.

### Base case: odd board

```python
if (rows * cols) % 2 == 1:
    return [], {
        "complete_tilings_checked": 0,
        "branches_pruned_by_fault_line": 0,
        "faultless_tilings_found": 0,
    }
```

A domino always covers 2 cells, so a board with an odd number of cells can never be fully tiled.

That means the function returns immediately.

---

## 8) Precomputing masks for the whole board

```python
total_cells = rows * cols
full_board = (1 << total_cells) - 1
full_row_crossed_mask = (1 << (rows - 1)) - 1
full_col_crossed_mask = (1 << (cols - 1)) - 1
row_masks, col_masks = make_crossing_masks(rows, cols)
```

This is the board state in binary.

### `full_board`

If a board is 10 x 10, then `full_board` is a bitmask with all 100 bits set to 1.

That means all cells are occupied.

### `full_row_crossed_mask`

If there are `rows - 1` internal horizontal lines, then the mask has that many bits set.

Example: for a 10x10 grid, there are 9 row lines.

### `full_col_crossed_mask`

Same idea, but for vertical internal lines.

---

## 9) The recursive backtracking search

```python
def backtrack(occupied, row_crossed_mask, col_crossed_mask):
```

This is the actual search algorithm.

### Step 1: stop if we already found one

```python
if stop_after_first and results:
    return
```

If we only want the first tiling, we stop exploring once we already found a valid one.

### Step 2: prune impossible branches early

```python
if prune_early and fault_line_is_unavoidable(
    occupied, row_crossed_mask, col_crossed_mask, row_masks, col_masks
):
    stats["branches_pruned_by_fault_line"] += 1
    return
```

This is the big optimization. If a partial tiling is doomed, it stops right there.

### Step 3: base case: full board filled

```python
if occupied == full_board:
    stats["complete_tilings_checked"] += 1

    if (
        row_crossed_mask == full_row_crossed_mask
        and col_crossed_mask == full_col_crossed_mask
    ):
        stats["faultless_tilings_found"] += 1
        results.append(current_matching.copy())
    return
```

When every cell is covered:
- count this as a complete tiling
- if every internal line has been crossed, it counts as a faultless tiling
- save the matching list

The line check means:
- every horizontal gap was crossed at least once
- every vertical gap was crossed at least once

That is the “clean” condition.

---

## 10) Choosing the next empty cell

```python
empty_bits = full_board ^ occupied
first_empty_bit = empty_bits & -empty_bits
i = first_empty_bit.bit_length() - 1
r, c = divmod(i, cols)
```

This is a smart trick.

### Why not choose any empty cell?

The code picks the lowest-numbered empty cell, which is the first cell that is still unfilled.

This reduces duplicate work because it forces a canonical ordering.

### Example

If cell 17 is the first free cell, then:
- `i = 17`
- `r = 17 // cols`
- `c = 17 % cols`

That gives the row and column position.

---

## 11) Trying the two possible domino placements

### Horizontal domino option

```python
if c + 1 < cols:
    j = i + 1
    domino_mask = (1 << i) | (1 << j)
    if (occupied & domino_mask) == 0:
        current_matching.append(((r, c), (r, c + 1)))
        backtrack(
            occupied | domino_mask,
            row_crossed_mask,
            col_crossed_mask | (1 << c),
        )
        current_matching.pop()
```

This tries placing a horizontal domino at `(r, c)` and `(r, c + 1)`.

- `domino_mask` has both bits set
- if not already occupied, it makes the move
- it records the pairing in `current_matching`
- it recurses with the updated occupied mask
- it marks the vertical line `c` as crossed

This is because a horizontal domino crosses the boundary between column `c` and `c+1`.

### Vertical domino option

```python
if r + 1 < rows:
    j = i + cols
    domino_mask = (1 << i) | (1 << j)
    if (occupied & domino_mask) == 0:
        current_matching.append(((r, c), (r + 1, c)))
        backtrack(
            occupied | domino_mask,
            row_crossed_mask | (1 << r),
            col_crossed_mask,
        )
        current_matching.pop()
```

This tries placing a vertical domino downwards.

- it crosses the boundary between row `r` and `r+1`
- so it sets the appropriate bit in `row_crossed_mask`

This branch explores every legal placement of the next cell.

---

## 12) Why this is a backtracking algorithm

Backtracking means:
- try a placement
- recurse deeper
- if that path fails, undo the move and try another one

That is exactly what this code does:

```python
current_matching.append(...)
backtrack(...)
current_matching.pop()
```

The `pop()` undoes the last choice so the algorithm can try the other direction.

This is how a search tree is explored without keeping every branch permanently active.

---

## 13) What the `stats` dictionary is tracking

```python
stats = {
    "complete_tilings_checked": 0,
    "branches_pruned_by_fault_line": 0,
    "faultless_tilings_found": 0,
}
```

This collects information while searching:
- `complete_tilings_checked`: number of full board coverings checked
- `branches_pruned_by_fault_line`: how many bad partial arrangements were cut off early
- `faultless_tilings_found`: how many valid solutions matched the crossing condition

These stats are useful to understand efficiency and how much pruning is helping.

---

## 14) The main execution block

```python
if __name__ == "__main__":
    faultless_tilings, stats = find_faultless_tilings(
        ROWS,
        COLS,
        stop_after_first=STOP_AFTER_FIRST,
        prune_early=PRUNE_EARLY,
    )
```

This runs when you execute the script directly.

Then:

```python
if faultless_tilings:
    print(f"grid: {ROWS}x{COLS}, there is at least one clean tiling.")
    if SHOW_FIRST:
        show_matching(ROWS, COLS, faultless_tilings[0])
else:
    print(f"grid: {ROWS}x{COLS}, no clean tiling here.")
```

If a valid tiling exists, the script:
- prints a message
- draws the first valid matching

Finally:

```python
input("press enter to exit...")
```

This keeps the window open so you can see the image before the program closes.

---

## 15) Understanding the algorithm in plain English

This solver is doing this:

1. Start with an empty board.
2. Pick the first empty cell.
3. Try placing a domino either left-right or up-down.
4. Record which internal lines have been crossed.
5. Keep going until the board is full or a branch becomes impossible.
6. If the board is full and every internal fault line was crossed, record this as a valid tiling.
7. Stop early if requested.

It is a classic depth-first search with a smart pruning rule.

The special achievement here is that it does not enumerate every domino tiling. It actively avoids impossible partial tilings based on whether a gap still has a chance to be crossed.

---

## 16) What the second script is doing

File: `drawing 6x6 explanation.py`

This file is much simpler and is more of a demonstration piece than a solver.

### Basic setup

```python
import matplotlib.pyplot as plt
import networkx as nx
import math

rows, cols = 6, 6
G = nx.grid_2d_graph(rows, cols)
```

This creates a 6x6 grid graph.

### Layout positions

```python
pos = {(i, j): (j, -i) for i, j in G.nodes()}
```

This creates a dictionary mapping each node to a 2D coordinate for display.

The `-i` flips the graph vertically so it draws nicely.

### Blank graph with nodes only

```python
plt.figure(figsize=(8, 8))
G.clear_edges()
```

This empties all the edges so the graph is just a point grid.

### Node numbering

```python
numberToNode = {}
for node in range(rows * cols):
  numberToNode[node] = (node // rows, node % rows)
```

This converts a flat cell index into a grid coordinate.

This is the same kind of numbering system used in the solver. But here, it is just for demonstration.

### A manual list of pairs

```python
pairs = [[7,8], [9,10], [13,14], ...]
for pair in pairs:
  #G.add_edge(nTN[pair[0]], nTN[pair[1]])
  continue
```

This is a set of hand-picked pairs that were intended to be drawn as domino edges.

The `continue` means nothing is actually added right now, so the drawing stays mostly empty.

This script is like a scratch file or concept test for graph layout and node pairing.

---

## 17) A beginner-friendly mental model

Think of the main program as this:

- each cell is a square
- each domino is a pair of adjacent squares
- the computer tries every legal domino placement like a human exploring a puzzle
- it never wastes time on branches that cannot possibly finish

The bitmask system is just a compact way to say:
- “which cells are already taken?”
- “which internal lines have already been crossed?”

It is a very efficient way to represent board state.

---

## 18) The most important ideas to learn here

If you only remember a few ideas, remember these:

1. `backtracking` = try a move, then undo it and try another
2. `bitmasks` = compact binary representation of occupied cells or crossed lines
3. `pruning` = stop exploring branches that are already impossible
4. `fault lines` = internal boundaries that must be crossed at least once
5. `networkx` = draws graphs and grids visually

---

## 19) Summary

This project combines:
- combinatorial search
- optimized bitwise logic
- backtracking recursion
- branch pruning
- graph visualization

It is a good example of how Python can model a puzzle and solve it efficiently without brute-forcing everything blindly.

If you want to learn this deeply, the next step is to slow down and trace one small board manually with the `backtrack` function and watch how the masks change as each domino is placed.

---

## 20) Quick review of the most important code patterns

```python
occupied & domino_mask == 0
```
This checks whether the domino overlaps anything already placed.

```python
row_crossed_mask | (1 << r)
```
This marks a row boundary as crossed.

```python
current_matching.pop()
```
This undoes the last move during backtracking.

```python
if occupied == full_board:
```
This means the board is completely covered.

```python
if prune_early and fault_line_is_unavoidable(...):
```
This kills impossible search branches early.

---

If you want, I can also turn this into a more polished “study notes” version with:
- simpler definitions for each variable
- a line-by-line annotation of the main function
- a version written like a classroom lesson with examples on a 2x2 or 3x3 board
