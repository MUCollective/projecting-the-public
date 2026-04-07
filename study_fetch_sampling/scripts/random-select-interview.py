from __future__ import annotations
import random
import re
from typing import Dict, List, Set, Tuple
import pandas as pd

INPUT_CSV = "data/papers_coded.csv"
OUTPUT_CSV = "data/interview_sample_balanced.csv"

N_SAMPLE = 35
SEED = 44

COLS_TO_BALANCE = [
    "specified audience",
    "specified role of visualization",
    "evaluation setting",
    "evaluation measures",
]

def parse_labels(cell: object) -> List[str]:
    """
    Parse multi-label cells.
    Supports:
      - real line breaks
      - literal '\\n'
      - pipe separators |
      - semicolons ;
    Returns [] if empty.
    """
    if cell is None:
        return []
    s = str(cell)

    # Convert literal "\n" into real newline so splitlines / regex split works
    s = s.replace("\\n", "\n")

    # Split on newline(s), pipes, or semicolons
    parts = re.split(r"\n+|\s*\|\s*|\s*;\s*", s)

    cleaned: List[str] = []
    for p in parts:
        p = p.strip()
        # don't append an NA or no string
        if not p:
            continue
        if p.lower() in {"n/a", "na", "none"}:
            continue
        cleaned.append(p)
    
    # print(cell, parts, cleaned)
    return cleaned

def build_universe(df: pd.DataFrame, cols: List[str]) -> Dict[str, Set[str]]:
    universe: Dict[str, Set[str]] = {c: set() for c in cols}

    for c in cols:
        # print('COLUMN', c)
        for v in df[c].tolist():
            labs = parse_labels(v)
            if not labs:
                universe[c].add("__MISSING__")
            else:
                universe[c].update(labs)

    # print('UNIVERSE', universe)
    return universe

def row_categories(df: pd.DataFrame, row_idx: int, cols: List[str]) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    for c in cols:
        labs = parse_labels(df.at[row_idx, c])
        out[c] = set(labs) if labs else {"__MISSING__"}
    return out

def greedy_cover_sample(
    df: pd.DataFrame,
    cols: List[str],
    n: int,
    seed: int,
) -> Tuple[pd.DataFrame, Dict[str, Set[str]], Dict[str, Set[str]]]:
    """
    Greedy set-cover sampling to maximize category coverage across cols.
    Tries to cover *all* categories per column; if impossible within n, maximizes coverage.

    Returns:
      sampled_df, covered_by_col, uncovered_by_col
    """
    rng = random.Random(seed)

    # Precompute per-row categories
    per_row = {i: row_categories(df, i, cols) for i in df.index}

    universe = build_universe(df, cols)
    covered: Dict[str, Set[str]] = {c: set() for c in cols}

    selected: List[int] = []
    remaining = set(df.index.tolist())

    def score_row(i: int) -> int:
        # total number of *new* categories this row would add across all columns
        score = 0
        for c in cols:
            score += len(per_row[i][c] - covered[c])
        return score

    # Greedy phase: keep picking rows that add the most unseen categories
    while len(selected) < n and remaining:
        best_score = -1
        best_candidates: List[int] = []

        for i in remaining:
            s = score_row(i)
            if s > best_score:
                best_score = s
                best_candidates = [i]
            elif s == best_score:
                best_candidates.append(i)

        # If no row adds any new category, stop greedy phase
        if best_score <= 0:
            break

        pick = rng.choice(best_candidates)
        selected.append(pick)
        remaining.remove(pick)

        for c in cols:
            covered[c].update(per_row[pick][c])

    # Fill remainder randomly (still “random sample”, but coverage-informed)
    if len(selected) < n and remaining:
        need = n - len(selected)
        selected.extend(rng.sample(list(remaining), k=min(need, len(remaining))))

    sampled = df.loc[selected].copy().reset_index(drop=True)
    uncovered = {c: (universe[c] - covered[c]) for c in cols}
    
    return sampled, covered, uncovered

def coverage_report(df_full: pd.DataFrame, df_sample: pd.DataFrame, cols: List[str]) -> None:
    print("\n=== Coverage report ===")
    for c in cols:
        universe_c = build_universe(df_full, [c])[c]
        covered_c = build_universe(df_sample, [c])[c]

        missing = universe_c - covered_c

        print(f"\n{c}")
        print(f"  total categories in dataset: {len(universe_c)}")
        print(f"  categories represented in sample: {len(covered_c)}")
        if missing:
            print(f"  ⚠️ missing categories (likely due to N=35 constraint): {sorted(missing)}")

def main():
    df = pd.read_csv(INPUT_CSV, dtype=str, keep_default_na=False)

    # Validate columns exist
    missing_cols = [c for c in COLS_TO_BALANCE if c not in df.columns]
    if missing_cols:
        raise ValueError(
            "CSV is missing these columns (check spelling/characters like en-dash): "
            + ", ".join(missing_cols)
        )

    sampled, covered, uncovered = greedy_cover_sample(
        df=df,
        cols=COLS_TO_BALANCE,
        n=N_SAMPLE,
        seed=SEED,
    )

    sampled.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Wrote sample of {len(sampled)} rows to: {OUTPUT_CSV}")
    print(f"Covered: {covered}")
    print(f"Uncovered: {uncovered}")

    coverage_report(df, sampled, COLS_TO_BALANCE)

if __name__ == "__main__":
    main()
