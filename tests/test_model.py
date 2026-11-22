"""Тесты модели Point и Map."""

import dataclasses

import pytest

from fdf.model import Map, Point


def test_len(elem: Map) -> None:
    assert len(elem) == 25


def test_iteration_order(elem: Map) -> None:
    points = [p for p in elem]
    assert len(points) == 25
    assert (points[0].x, points[0].y) == (0, 0)
    assert (points[1].x, points[1].y) == (1, 0)
    assert (points[-1].x, points[-1].y) == (4, 4)


def test_neighbors_of_corner(elem: Map) -> None:
    corner = elem[0, 0]
    assert set(elem.neighbors(corner)) == {elem[1, 0], elem[0, 1]}
    last = elem[4, 4]
    assert set(elem.neighbors(last)) == {elem[3, 4], elem[4, 3]}


def test_neighbors_of_inner_point(elem: Map) -> None:
    assert len(elem.neighbors(elem[2, 2])) == 4


def test_edges_each_once(elem: Map) -> None:
    edges = list(elem.edges())
    # (w-1)·h горизонтальных + w·(h-1) вертикальных
    assert len(edges) == 4 * 5 + 5 * 4
    assert len({(a.x, a.y, b.x, b.y) for a, b in edges}) == len(edges)


def test_single_point_map() -> None:
    m = Map([[Point(0, 0, 3)]])
    assert len(m) == 1
    assert m.neighbors(m[0, 0]) == []
    assert list(m.edges()) == []


def test_contains_getitem_and_bounds(elem: Map) -> None:
    assert elem[2, 2] in elem
    assert Point(2, 2, 99) not in elem
    with pytest.raises(IndexError):
        elem[5, 0]


def test_point_is_immutable() -> None:
    p = Point(1, 2, 3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.z = 4  # type: ignore[misc]


def test_map_rejects_bad_rows() -> None:
    with pytest.raises(ValueError):
        Map([])
    with pytest.raises(ValueError):
        Map([[Point(0, 0, 0)], [Point(0, 1, 0), Point(1, 1, 0)]])


def test_repr_and_eq(elem: Map) -> None:
    assert repr(elem) == "Map(width=5, height=5)"
    assert elem == Map([[elem[x, y] for x in range(5)] for y in range(5)])
