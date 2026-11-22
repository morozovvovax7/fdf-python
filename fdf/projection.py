"""Изометрическая проекция точек карты на плоскость окна.

Модуль не зависит от графической библиотеки: он вычисляет экранные
координаты, а рисует их интерфейс (fdf/app.py).
"""

import math
from collections.abc import Iterator
from dataclasses import dataclass

from fdf.model import Map, Point

ISO_ANGLE = math.pi / 6  # 30°
FIT_MARGIN = 0.9

DEFAULT_COLOR = "#FFFFFF"


@dataclass(frozen=True, slots=True)
class Segment:
    """Отрезок на экране, готовый к отрисовке."""

    x0: float
    y0: float
    x1: float
    y1: float
    color: str


@dataclass
class Camera:
    """Параметры проекции и преобразования в координаты окна.

    x′ = (x − y) · cos(angle)
    y′ = (x + y) · sin(angle) − z · z_scale
    X = x′ · scale + offset_x,  Y = y′ · scale + offset_y
    """

    scale: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    z_scale: float = 1.0
    angle: float = ISO_ANGLE

    def project_raw(self, point: Point) -> tuple[float, float]:
        """Координаты (x′, y′) на плоскости до масштабирования и сдвига."""
        px = (point.x - point.y) * math.cos(self.angle)
        py = (point.x + point.y) * math.sin(self.angle) - point.z * self.z_scale
        return px, py

    def project(self, point: Point) -> tuple[float, float]:
        """Экранные координаты (X, Y) точки."""
        px, py = self.project_raw(point)
        return px * self.scale + self.offset_x, py * self.scale + self.offset_y

    def bounds(self, map_: Map) -> tuple[float, float, float, float]:
        """Ограничивающий прямоугольник (min_x, min_y, max_x, max_y) при scale = 1."""
        xs: list[float] = []
        ys: list[float] = []
        for point in map_:
            px, py = self.project_raw(point)
            xs.append(px)
            ys.append(py)
        return min(xs), min(ys), max(xs), max(ys)

    def center(self, map_: Map, width: int, height: int) -> None:
        """Подобрать смещение так, чтобы карта была в центре окна (scale не меняется)."""
        min_x, min_y, max_x, max_y = self.bounds(map_)
        self.offset_x = width / 2 - (min_x + max_x) / 2 * self.scale
        self.offset_y = height / 2 - (min_y + max_y) / 2 * self.scale

    def fit(self, map_: Map, width: int, height: int) -> None:
        """Подобрать scale и смещение, чтобы карта заняла 90 % окна и была по центру."""
        min_x, min_y, max_x, max_y = self.bounds(map_)
        span_x = max_x - min_x
        span_y = max_y - min_y
        candidates: list[float] = []
        if span_x > 0:
            candidates.append(width / span_x)
        if span_y > 0:
            candidates.append(height / span_y)
        # Карта из одной точки (или вырожденная) — масштаб не важен.
        self.scale = min(candidates) * FIT_MARGIN if candidates else 1.0
        self.center(map_, width, height)


def point_color(point: Point) -> str:
    """Цвет точки: из файла, иначе цвет по умолчанию."""
    return point.color if point.color is not None else DEFAULT_COLOR


def segments(map_: Map, camera: Camera) -> Iterator[Segment]:
    """Отрезки каркаса в координатах окна; каждое ребро — ровно один раз."""
    cache = {(p.x, p.y): camera.project(p) for p in map_}
    for a, b in map_.edges():
        x0, y0 = cache[a.x, a.y]
        x1, y1 = cache[b.x, b.y]
        yield Segment(x0, y0, x1, y1, point_color(a))
