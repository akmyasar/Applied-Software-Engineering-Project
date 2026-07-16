"""Vector figures for the report.

Each figure is drawn with matplotlib, written out as SVG and converted into a
ReportLab drawing, so the chart stays vector inside the final PDF and can be
zoomed without pixelation (Part 2 Step 4d a. iii).

Text is emitted as paths (`svg.fonttype = "path"`), which keeps the rendering
identical to the matplotlib output instead of depending on which fonts the SVG
converter can resolve.
"""
import io
import textwrap

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "path"
matplotlib.rcParams["font.family"] = "DejaVu Sans"

import matplotlib.pyplot as plt
from svglib.svglib import svg2rlg

from part2 import isic

BAR_COLOR = "#2F5496"
BAR_EDGE = "#1F3864"
GRID_COLOR = "#BFBFBF"
TEXT_COLOR = "#404040"


# Step 4d requires the *full* class name as the bin name, so the wrap has to be
# able to hold the longest one ISIC Rev. 5 has - division 16 runs to 129
# characters. 3 x 44 leaves room for it without ever truncating.
LABEL_WRAP = 44
LABEL_LINES = 3


def wrap_label(text, width=LABEL_WRAP, max_lines=LABEL_LINES):
    """Stack a long class name over several lines so one label cannot eat half
    the figure. Truncation is a last resort and would breach the spec, so the
    defaults are sized to make it unreachable."""
    # break_on_hyphens would split "non-residential buildings" across lines as
    # "non-" / "residential", which silently rewrites the class name it is
    # supposed to reproduce verbatim.
    lines = textwrap.wrap(text, width=width, break_on_hyphens=False)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: width - 1] + "…"
    return "\n".join(lines)


def _to_drawing(figure):
    buffer = io.StringIO()
    figure.savefig(buffer, format="svg", bbox_inches="tight")
    plt.close(figure)
    return svg2rlg(io.BytesIO(buffer.getvalue().encode("utf-8")))


def scale_to_width(drawing, target_width, max_height=None):
    """Fit a drawing to the frame while preserving its aspect ratio."""
    factor = target_width / drawing.width
    if max_height and drawing.height * factor > max_height:
        factor = max_height / drawing.height
    drawing.width *= factor
    drawing.height *= factor
    drawing.scale(factor, factor)
    return drawing


MM_PER_INCH = 25.4


def class_histogram(counts, width_mm, height_mm):
    """Histogram of primary classes, sized to fill the page it is placed on.

    The bin name is the full ISIC class name and the count is printed on top of
    each bar, as required by Step 4d.

    The figure is built at the physical size it will occupy, so the point sizes
    chosen here survive into the PDF instead of being scaled to something
    unreadable afterwards.
    """
    ordered = counts.most_common()
    # Few wide lines rather than many narrow ones. Rotated labels are anchored at
    # their tick, so neighbours are parallel and separated by
    # bar_spacing x sin(45 deg); a label overlaps its neighbour once its block of
    # wrapped lines grows thicker than that gap. A narrow wrap makes the axis
    # unreadable for exactly this reason.
    labels = [wrap_label(isic.full_class_name(code)) for code, _ in ordered]
    values = [n for _, n in ordered]

    figure, axes = plt.subplots(
        figsize=(width_mm / MM_PER_INCH, height_mm / MM_PER_INCH))

    bars = axes.bar(range(len(values)), values,
                    color=BAR_COLOR, edgecolor=BAR_EDGE, linewidth=0.6, width=0.66)
    headroom = max(values) * 0.02
    for bar, value in zip(bars, values):
        axes.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + headroom,
                  f"{value:,}", ha="center", va="bottom",
                  fontsize=7, fontweight="bold", color=TEXT_COLOR)

    # Bins get closer together as they multiply, so the label size follows the
    # bin count rather than being fixed.
    label_size = 6.0 if len(labels) <= 14 else (5.4 if len(labels) <= 22 else 4.6)
    axes.set_xticks(range(len(labels)))
    axes.set_xticklabels(labels, rotation=45, ha="right", fontsize=label_size,
                         rotation_mode="anchor", color=TEXT_COLOR)
    axes.set_ylabel("Number of projects", fontsize=7.5, color=TEXT_COLOR)
    axes.set_ylim(0, max(values) * 1.16)
    axes.tick_params(axis="y", labelsize=6.5, colors=TEXT_COLOR)
    axes.spines[["top", "right"]].set_visible(False)
    axes.spines[["left", "bottom"]].set_color(GRID_COLOR)
    axes.grid(axis="y", linestyle=":", color=GRID_COLOR, alpha=0.8)
    axes.set_axisbelow(True)
    figure.tight_layout(pad=0.6)

    return scale_to_width(_to_drawing(figure), width_mm * 72 / MM_PER_INCH,
                          height_mm * 72 / MM_PER_INCH)


def type_bar(type_counts, order, target_width, max_height=None):
    """Small horizontal bar of the PROJECT_TYPE distribution."""
    labels = [t for t in order if type_counts.get(t)]
    values = [type_counts[t] for t in labels]

    figure, axes = plt.subplots(figsize=(6.4, 0.52 * len(labels) + 0.9))
    bars = axes.barh(range(len(values)), values, color=BAR_COLOR,
                     edgecolor=BAR_EDGE, linewidth=0.6, height=0.6)
    axes.invert_yaxis()
    for bar, value in zip(bars, values):
        axes.text(bar.get_width() + max(values) * 0.012,
                  bar.get_y() + bar.get_height() / 2, f"{value:,}",
                  va="center", ha="left", fontsize=8, fontweight="bold",
                  color=TEXT_COLOR)

    axes.set_yticks(range(len(labels)))
    axes.set_yticklabels(labels, fontsize=8, color=TEXT_COLOR)
    axes.set_xlim(0, max(values) * 1.12)
    axes.set_xlabel("Number of projects", fontsize=8, color=TEXT_COLOR)
    axes.tick_params(axis="x", labelsize=7, colors=TEXT_COLOR)
    axes.spines[["top", "right", "left"]].set_visible(False)
    axes.spines["bottom"].set_color(GRID_COLOR)
    axes.grid(axis="x", linestyle=":", color=GRID_COLOR, alpha=0.8)
    axes.set_axisbelow(True)
    figure.tight_layout()

    return scale_to_width(_to_drawing(figure), target_width, max_height)
