"""Тесты цвета: интерполяция, палитра по высоте, градиент вдоль рёбер."""

from pathlib import Path

import pytest

from fdf.model import Map, Point
from fdf.parser import load_map
from fdf.projection import (
    DEFAULT_COLOR,
    HEIGHT_PALETTE,
    Camera,
    Segment,
    gradient,
    height_color,
    lerp_color,
    point_color,
    segments,
)


@pytest.mark.parametrize(
    ("a", "b", "t", "expected"),
    [
        ("#000000", "#FFFFFF", 0.0, "#000000"),
        ("#000000", "#FFFFFF", 1.0, "#FFFFFF"),
        ("#000000", "#FFFFFF", 0.5, "#808080"),
        ("#FF0000", "#0000FF", 0.25, "#BF0040"),
        ("#102030", "#102030", 0.7, "#102030"),
        ("#000000", "#FFFFFF", 2.0, "#FFFFFF"),  # t ограничивается отрезком [0, 1]
    ],
)
def test_lerp_color(a: str, b: str, t: float, expected: str) -> None:
    assert lerp_color(a, b, t) == expected


def test_height_color_ends_and_flat() -> None:
    assert height_color(0, 0, 10) == HEIGHT_PALETTE[0]
    assert height_color(10, 0, 10) == HEIGHT_PALETTE[-1]
    assert height_color(5, 5, 5) == HEIGHT_PALETTE[0]


def test_height_color_middle_point_of_palette() -> None:
    # 4 опорных цвета → t = 1/3 даёт ровно второй цвет палитры.
    assert height_color(1, 0, 3) == HEIGHT_PALETTE[1]


def test_point_color_priority() -> None:
    m = Map([[Point(0, 0, 0), Point(1, 0, 10, "#FF0000")]])
    assert point_color(m[1, 0], m) == "#FF0000"
    assert point_color(m[0, 0], m) == HEIGHT_PALETTE[0]
    assert point_color(m[0, 0], m, mode="file") == DEFAULT_COLOR


def test_flat_map_uses_default_color() -> None:
    m = Map([[Point(0, 0, 0), Point(1, 0, 0)]])
    assert point_color(m[0, 0], m) == DEFAULT_COLOR


def test_gradient_splits_edge_and_keeps_endpoints() -> None:
    seg = Segment(0, 0, 100, 0, "#000000")
    parts = list(gradient(seg, "#FFFFFF"))
    assert len(parts) > 1
    assert parts[0].x0 == 0
    assert parts[-1].x1 == pytest.approx(100)
    assert parts[0].color < parts[-1].color  # от тёмного к светлому
    assert len(list(gradient(seg, "#000000"))) == 1


def test_peak_map_colors(maps_dir: Path) -> None:
    m = load_map(maps_dir / "peak.fdf")
    assert m[3, 3].color == "#FF0000"
    assert m[0, 0].color == "#0000FF"  # короткая запись 0xff
    assert m[2, 2].color is None
    camera = Camera()
    camera.fit(m, 800, 600)
    segs = list(segments(m, camera))
    assert len(segs) > len(list(m.edges()))  # есть рёбра с градиентом
