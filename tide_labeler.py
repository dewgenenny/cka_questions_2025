"""
CLI utility to re-label a tidal calendar so that only the strongest spring
and neap tides in each cycle are marked.

The previous labeling logic marked multiple consecutive days as either spring
or neap. This tool smooths the series of daily maximum heights and only marks
turning points (local peaks or troughs) once per monotonic run, which keeps
exactly one spring and one neap per cycle while tolerating minor day-to-day
noise.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


@dataclass
class TideDay:
    date: str
    raw: dict
    max_height: float
    label: str = ""


HEIGHT_KEYS = ("Tide1 Height(ft)", "Tide2 Height(ft)")
LABEL_KEY = "Neap/Spring"
SPRING_MARK = "\u25cf Spring"
NEAP_MARK = "\u25cb Neap"


def parse_height(value: str) -> Optional[float]:
    """Convert a tide height string into a float if present."""

    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return float(value)


def load_tides(path: str) -> List[TideDay]:
    """Read the CSV and compute the maximum tide height for each day."""

    days: List[TideDay] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            heights = [parse_height(row.get(key, "")) for key in HEIGHT_KEYS]
            max_height = max([h for h in heights if h is not None]) if any(
                h is not None for h in heights
            ) else 0.0
            days.append(TideDay(date=row.get("Date", ""), raw=row, max_height=max_height))
    return days


def _extreme_index(
    heights: Sequence[float], start: int, end: int, pick_min: bool
) -> int:
    span = range(start, end)
    key_fn = (min if pick_min else max)
    extreme_val = key_fn(heights[i] for i in span)
    for i in span:
        if abs(heights[i] - extreme_val) < 1e-9:
            return i
    return start


def label_tides(heights: Sequence[float], tolerance: float = 0.1) -> List[str]:
    """Assign spring/neap labels using local extrema detection.

    The algorithm builds monotonic runs while ignoring tiny day-to-day changes
    (controlled by ``tolerance``). A spring tide is marked at the peak of an
    increasing run that starts decreasing, while a neap tide is marked at the
    trough of a decreasing run that starts increasing. Only one label is
    produced per run, which prevents long streaks of the same label.
    """

    n = len(heights)
    labels = ["" for _ in range(n)]
    if n == 0:
        return labels

    trend: Optional[int] = None  # 1 for rising, -1 for falling
    run_start = 0

    def diff_sign(delta: float) -> int:
        if abs(delta) <= tolerance:
            return 0
        return 1 if delta > 0 else -1

    for i in range(1, n):
        step = diff_sign(heights[i] - heights[i - 1])
        if step == 0:
            continue
        if trend is None:
            trend = step
            run_start = i - 1
            continue
        if step != trend:
            if trend > 0:
                idx = _extreme_index(heights, run_start, i + 1, pick_min=False)
                labels[idx] = SPRING_MARK
            else:
                idx = _extreme_index(heights, run_start, i + 1, pick_min=True)
                labels[idx] = NEAP_MARK
            trend = step
            run_start = i - 1

    if not any(labels) and n:
        # If the series never reversed direction enough to trigger a label,
        # fall back to marking the global high/low pair when they differ by
        # more than the tolerated noise.
        max_height = max(heights)
        min_height = min(heights)
        if max_height - min_height > tolerance:
            labels[heights.index(max_height)] = SPRING_MARK
            labels[heights.index(min_height)] = NEAP_MARK

    return labels


def apply_labels(days: Iterable[TideDay], tolerance: float = 0.1) -> List[TideDay]:
    days_list = list(days)
    heights = [day.max_height for day in days_list]
    labels = label_tides(heights, tolerance=tolerance)
    for day, label in zip(days_list, labels):
        day.label = label
    return days_list


def write_csv(days: Iterable[TideDay], path: str) -> None:
    days_list = list(days)
    if not days_list:
        return
    fieldnames = list(days_list[0].raw.keys())
    if LABEL_KEY not in fieldnames:
        fieldnames.insert(1, LABEL_KEY)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for day in days_list:
            row = dict(day.raw)
            row[LABEL_KEY] = day.label
            writer.writerow(row)


def write_stdout(days: Iterable[TideDay]) -> None:
    days_list = list(days)
    if not days_list:
        return
    fieldnames = list(days_list[0].raw.keys())
    if LABEL_KEY not in fieldnames:
        fieldnames.insert(1, LABEL_KEY)

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    for day in days_list:
        row = dict(day.raw)
        row[LABEL_KEY] = day.label
        writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the tidal CSV")
    parser.add_argument(
        "-o",
        "--output",
        help="File to write corrected labels to (defaults to stdout)",
        default="",
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        type=float,
        default=0.1,
        help="Height difference (ft) treated as noise when detecting turning points",
    )
    args = parser.parse_args()

    days = load_tides(args.input)
    labeled = apply_labels(days, tolerance=args.tolerance)

    if args.output:
        write_csv(labeled, args.output)
    else:
        write_stdout(labeled)


if __name__ == "__main__":
    main()
