"""Изометрическая проекция точек карты на плоскость окна.

Модуль не зависит от графической библиотеки: он вычисляет экранные
координаты, а рисует их интерфейс (fdf/app.py).
"""

import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Literal

from fdf.model import Map, Point

ISO_ANGLE = math.pi / 6  # 30°
FIT_MARGIN = 0.9
MIN_SCALE = 1e-3
MAX_SCALE = 1e5

DEFAULT_COLOR = "#FFFFFF"
# Палитра по высоте: синий → зелёный → жёлтый → красный.
HEIGHT_PALETTE: tuple[str, ...] = ("#2B6CFF", "#22C55E", "#FACC15", "#EF4444")
# Длина (в пикселях) одного кусочка ребра при градиенте и предел числа кусочков.
GRADIENT_PIECE = 6.0
GRADIENT_MAX_PIECES = 16

ColorMode = Literal["height", "file"]


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
    parallel: bool = False  # вид сверху: X = x, Y = y без учёта z

    def project_raw(self, point: Point) -> tuple[float, float]:
        """Координаты (x′, y′) на плоскости до масштабирования и сдвига."""
        if self.parallel:
            return float(point.x), float(point.y)
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

    def zoom(self, factor: float, cx: float, cy: float) -> None:
        """Умножить scale на factor, оставив точку экрана (cx, cy) на месте."""
        new_scale = min(max(self.scale * factor, MIN_SCALE), MAX_SCALE)
        k = new_scale / self.scale
        self.offset_x = cx - (cx - self.offset_x) * k
        self.offset_y = cy - (cy - self.offset_y) * k
        self.scale = new_scale

    def move(self, dx: float, dy: float) -> None:
        """Сдвинуть изображение на (dx, dy) пикселей."""
        self.offset_x += dx
        self.offset_y += dy


def _rgb(color: str) -> tuple[int, int, int]:
    value = int(color.lstrip("#"), 16)
    return (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF


def lerp_color(a: str, b: str, t: float) -> str:
    """Линейная интерполяция цвета по каналам: C = (1 − t)·A + t·B, t ∈ [0, 1]."""
    t = min(max(t, 0.0), 1.0)
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    r = round(ra + (rb - ra) * t)
    g = round(ga + (gb - ga) * t)
    bl = round(ba + (bb - ba) * t)
    return f"#{r:02X}{g:02X}{bl:02X}"


def height_color(
    z: float, z_min: float, z_max: float, palette: Sequence[str] = HEIGHT_PALETTE
) -> str:
    """Цвет по высоте: t = (z − z_min) / (z_max − z_min), интерполяция по палитре."""
    if z_max <= z_min:
        return palette[0]
    t = min(max((z - z_min) / (z_max - z_min), 0.0), 1.0)
    position = t * (len(palette) - 1)
    index = min(int(position), len(palette) - 2)
    return lerp_color(palette[index], palette[index + 1], position - index)


def point_color(point: Point, map_: Map | None = None, mode: ColorMode = "height") -> str:
    """Цвет точки: из файла; иначе по высоте (mode="height") или цвет по умолчанию.

    На плоской карте цвет по высоте не имеет смысла — используется цвет по умолчанию.
    """
    if point.color is not None:
        return point.color
    if mode == "height" and map_ is not None and map_.z_max > map_.z_min:
        return height_color(point.z, map_.z_min, map_.z_max)
    return DEFAULT_COLOR


def gradient(seg: Segment, end_color: str) -> Iterator[Segment]:
    """Разбить отрезок на кусочки с цветом от seg.color к end_color.

    Число кусочков зависит от длины отрезка на экране, поэтому на крупных
    картах (где рёбра короткие) лишней работы нет.
    """
    if seg.color == end_color:
        yield seg
        return
    length = math.hypot(seg.x1 - seg.x0, seg.y1 - seg.y0)
    n = min(max(int(length / GRADIENT_PIECE), 1), GRADIENT_MAX_PIECES)
    if n == 1:
        yield Segment(seg.x0, seg.y0, seg.x1, seg.y1, lerp_color(seg.color, end_color, 0.5))
        return
    dx = (seg.x1 - seg.x0) / n
    dy = (seg.y1 - seg.y0) / n
    for k in range(n):
        color = lerp_color(seg.color, end_color, (k + 0.5) / n)
        yield Segment(
            seg.x0 + dx * k, seg.y0 + dy * k, seg.x0 + dx * (k + 1), seg.y0 + dy * (k + 1), color
        )


def segments(map_: Map, camera: Camera, color_mode: ColorMode = "height") -> Iterator[Segment]:
    """Отрезки каркаса в координатах окна; каждое ребро — ровно один раз.

    Ребро с разными цветами концов разбивается на кусочки с градиентом.
    """
    cache = {(p.x, p.y): (camera.project(p), point_color(p, map_, color_mode)) for p in map_}
    for a, b in map_.edges():
        (x0, y0), color_a = cache[a.x, a.y]
        (x1, y1), color_b = cache[b.x, b.y]
        yield from gradient(Segment(x0, y0, x1, y1, color_a), color_b)
