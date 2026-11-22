"""Тесты проекции и Camera.fit."""

import math
from pathlib import Path

import pytest

from fdf.model import Map, Point
from fdf.parser import load_map
from fdf.projection import Camera, segments


def test_origin_projects_to_origin() -> None:
    assert Camera().project(Point(0, 0, 0)) == (0.0, 0.0)


def test_height_goes_up() -> None:
    _, y = Camera().project(Point(0, 0, 1))
    assert y < 0


def test_isometric_formula() -> None:
    x, y = Camera().project(Point(2, 0, 0))
    assert x == pytest.approx(2 * math.cos(math.pi / 6))
    assert y == pytest.approx(2 * math.sin(math.pi / 6))


@pytest.mark.parametrize("name", ["elem.fdf", "42.fdf", "flat.fdf", "hills.fdf"])
@pytest.mark.parametrize(("width", "height"), [(800, 600), (300, 900), (1920, 200)])
def test_fit_keeps_points_inside_window(name: str, width: int, height: int) -> None:
    m = load_map(Path(__file__).resolve().parent.parent / "maps" / name)
    camera = Camera()
    camera.fit(m, width, height)
    for point in m:
        x, y = camera.project(point)
        assert 0 <= x <= width
        assert 0 <= y <= height


def test_fit_centers_flat_map_symmetrically(maps_dir: Path) -> None:
    m = load_map(maps_dir / "flat.fdf")
    camera = Camera()
    camera.fit(m, 800, 600)
    xs = [camera.project(p)[0] for p in m]
    assert (min(xs) + max(xs)) / 2 == pytest.approx(400)
    # Ромб: верхняя и нижняя вершины лежат на вертикальной оси окна.
    top = camera.project(m[0, 0])
    bottom = camera.project(m[m.width - 1, m.height - 1])
    assert top[0] == pytest.approx(400)
    assert bottom[0] == pytest.approx(400)


def test_fit_single_point_map() -> None:
    m = Map([[Point(0, 0, 7)]])
    camera = Camera()
    camera.fit(m, 640, 480)
    assert camera.project(m[0, 0]) == pytest.approx((320, 240))


def test_segments_one_per_edge(elem: Map) -> None:
    camera = Camera()
    camera.fit(elem, 500, 500)
    assert len(list(segments(elem, camera))) == len(list(elem.edges()))
