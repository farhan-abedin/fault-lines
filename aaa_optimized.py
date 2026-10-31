import matplotlib.pyplot as plt
import networkx as nx


ROWS, COLS = 10, 10
STOP_AFTER_FIRST = True  # stop at the first hit
PRUNE_EARLY = True  # drop a branch once some line can't be crossed any more
SHOW_FIRST = True  # show the first tiling found


def show_matching(rows, cols, matching):
    """draw one tiling"""
    G = nx.grid_2d_graph(rows, cols)
    pos = {(i, j): (j, -i) for i, j in G.nodes()}

    plt.figure(figsize=(8, 8))
    nx.draw_networkx_nodes(G, pos, node_color="black", node_size=100)
    nx.draw_networkx_edges(G, pos, edgelist=matching, edge_color="red", width=3)
    plt.axis("off")
    plt.show()


def make_crossing_masks(rows, cols):
    """bitmasks of every domino that can cross each internal line.
    row_masks[r]: vertical dominoes between rows r and r+1, col_masks[c]: horizontal ones between cols c and c+1"""
    row_masks = [[] for _ in range(rows - 1)]
    col_masks = [[] for _ in range(cols - 1)]

    for r in range(rows - 1):
        for c in range(cols):
            a = r * cols + c
            b = (r + 1) * cols + c
            row_masks[r].append((1 << a) | (1 << b))

    for r in range(rows):
        for c in range(cols - 1):
            a = r * cols + c
            b = r * cols + (c + 1)
            col_masks[c].append((1 << a) | (1 << b))

    return row_masks, col_masks


def line_can_still_be_crossed(occupied, possible_domino_masks):
    return any((occupied & domino_mask) == 0 for domino_mask in possible_domino_masks)


def fault_line_is_unavoidable(occupied, row_crossed_mask, col_crossed_mask, row_masks, col_masks):
    """true if some line hasn't been crossed yet and no domino can cross it anymore"""
    for r, possible_domino_masks in enumerate(row_masks):
        if not (row_crossed_mask & (1 << r)):
            if not line_can_still_be_crossed(occupied, possible_domino_masks):
                return True

    for c, possible_domino_masks in enumerate(col_masks):
        if not (col_crossed_mask & (1 << c)):
            if not line_can_still_be_crossed(occupied, possible_domino_masks):
                return True

    return False


def find_faultless_tilings(rows, cols, stop_after_first=True, prune_early=True):
    """domino tilings of a rows x cols grid where every internal line is crossed by at least one domino"""
    if (rows * cols) % 2 == 1:
        return [], {
            "complete_tilings_checked": 0,
            "branches_pruned_by_fault_line": 0,
            "faultless_tilings_found": 0,
        }

    total_cells = rows * cols
    full_board = (1 << total_cells) - 1
    full_row_crossed_mask = (1 << (rows - 1)) - 1
    full_col_crossed_mask = (1 << (cols - 1)) - 1
    row_masks, col_masks = make_crossing_masks(rows, cols)

    results = []
    current_matching = []
    stats = {
        "complete_tilings_checked": 0,
        "branches_pruned_by_fault_line": 0,
        "faultless_tilings_found": 0,
    }

    def backtrack(occupied, row_crossed_mask, col_crossed_mask):
        if stop_after_first and results:
            return

        if prune_early and fault_line_is_unavoidable(
            occupied, row_crossed_mask, col_crossed_mask, row_masks, col_masks
        ):
            stats["branches_pruned_by_fault_line"] += 1
            return

        if occupied == full_board:
            stats["complete_tilings_checked"] += 1

            if (
                row_crossed_mask == full_row_crossed_mask
                and col_crossed_mask == full_col_crossed_mask
            ):
                stats["faultless_tilings_found"] += 1
                results.append(current_matching.copy())
            return

        # always fill the first empty cell, avoids counting the same tiling twice
        empty_bits = full_board ^ occupied
        first_empty_bit = empty_bits & -empty_bits
        i = first_empty_bit.bit_length() - 1
        r, c = divmod(i, cols)

        # horizontal
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

        # vertical
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

    backtrack(occupied=0, row_crossed_mask=0, col_crossed_mask=0)
    return results, stats


if __name__ == "__main__":
    faultless_tilings, stats = find_faultless_tilings(
        ROWS,
        COLS,
        stop_after_first=STOP_AFTER_FIRST,
        prune_early=PRUNE_EARLY,
    )

    # print(f"tilings checked: {stats['complete_tilings_checked']}")
    # print(f"dead branches cut: {stats['branches_pruned_by_fault_line']}")
    # print(f"clean tilings found: {stats['faultless_tilings_found']}")

    if faultless_tilings:
        print(f"grid: {ROWS}x{COLS}, there is at least one clean tiling.")
        if SHOW_FIRST:
            show_matching(ROWS, COLS, faultless_tilings[0])
    else:
        print(f"grid: {ROWS}x{COLS}, no clean tiling here.")

    input("press enter to exit...")
