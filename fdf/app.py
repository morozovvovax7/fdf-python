"""Графический интерфейс на tkinter.

Единственный модуль, который импортирует графическую библиотеку.
"""

import math
import tkinter as tk

from fdf.model import Map
from fdf.projection import ISO_ANGLE, Camera, segments

BACKGROUND = "#0E1729"
HUD_COLOR = "#7A8599"

ZOOM_STEP = 1.15
MOVE_STEP = 30.0
Z_STEP = 1.25
ANGLE_STEP = math.radians(5)
ANGLE_MIN = 0.0
ANGLE_MAX = math.pi / 2

HELP = (
    "колесо — масштаб · стрелки — сдвиг · +/− — высота · "
    "Q/E — угол · P — вид сверху · R — сброс · Esc — выход"
)


class App:
    """Окно с каркасной моделью карты."""

    def __init__(self, map_: Map, title: str = "FdF", width: int = 1200, height: int = 800) -> None:
        self.map = map_
        self.camera = Camera()
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(200, 150)
        self.canvas = tk.Canvas(self.root, bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.width = width
        self.height = height
        self._redraw_pending = False

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", lambda _event: self.close())
        self.root.bind("<Key>", self._on_key)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<MouseWheel>", self._on_wheel)  # Windows, macOS
        self.canvas.bind("<Button-4>", self._on_wheel)  # Linux: вверх
        self.canvas.bind("<Button-5>", self._on_wheel)  # Linux: вниз

    def run(self) -> None:
        """Запустить главный цикл обработки событий."""
        self.root.mainloop()

    def close(self) -> None:
        """Закрыть окно и завершить работу."""
        self.root.destroy()

    def _on_resize(self, event: "tk.Event[tk.Canvas]") -> None:
        self.width = max(event.width, 1)
        self.height = max(event.height, 1)
        self.camera.fit(self.map, self.width, self.height)
        self.request_redraw()

    def _on_wheel(self, event: "tk.Event[tk.Canvas]") -> None:
        up = event.num == 4 or event.delta > 0
        self.camera.zoom(ZOOM_STEP if up else 1 / ZOOM_STEP, event.x, event.y)
        self.request_redraw()

    def _on_key(self, event: "tk.Event[tk.Misc]") -> None:
        if self.handle_key(event.keysym):
            self.request_redraw()

    def handle_key(self, keysym: str) -> bool:
        """Обработать клавишу; вернуть True, если изображение изменилось."""
        camera = self.camera
        moves = {
            "Left": (MOVE_STEP, 0.0),
            "Right": (-MOVE_STEP, 0.0),
            "Up": (0.0, MOVE_STEP),
            "Down": (0.0, -MOVE_STEP),
        }
        if keysym in moves:
            camera.move(*moves[keysym])
        elif keysym in ("plus", "equal", "KP_Add"):
            camera.z_scale *= Z_STEP
            camera.center(self.map, self.width, self.height)
        elif keysym in ("minus", "KP_Subtract"):
            camera.z_scale /= Z_STEP
            camera.center(self.map, self.width, self.height)
        elif keysym.lower() in ("q", "e"):
            step = -ANGLE_STEP if keysym.lower() == "q" else ANGLE_STEP
            camera.angle = min(max(camera.angle + step, ANGLE_MIN), ANGLE_MAX)
            camera.center(self.map, self.width, self.height)
        elif keysym.lower() == "p":
            camera.parallel = not camera.parallel
            camera.fit(self.map, self.width, self.height)
        elif keysym.lower() == "r":
            camera.z_scale = 1.0
            camera.angle = ISO_ANGLE
            camera.parallel = False
            camera.fit(self.map, self.width, self.height)
        else:
            return False
        return True

    def request_redraw(self) -> None:
        """Запланировать перерисовку (несколько запросов подряд объединяются)."""
        if not self._redraw_pending:
            self._redraw_pending = True
            self.root.after_idle(self.redraw)

    def redraw(self) -> None:
        """Перерисовать каркас."""
        self._redraw_pending = False
        self.canvas.delete("all")
        for seg in segments(self.map, self.camera):
            self.canvas.create_line(seg.x0, seg.y0, seg.x1, seg.y1, fill=seg.color)
        self.canvas.create_text(
            12,
            self.height - 12,
            anchor=tk.SW,
            fill=HUD_COLOR,
            font=("TkFixedFont", 10),
            text=self.hud_text(),
        )

    def hud_text(self) -> str:
        """Строка состояния в нижнем левом углу окна."""
        m = self.map
        c = self.camera
        view = "сверху" if c.parallel else f"угол {math.degrees(c.angle):.0f}°"
        return (
            f"{m.width}×{m.height} · z = {m.z_min}..{m.z_max} · "
            f"z_scale {c.z_scale:.2f} · {view}\n{HELP}"
        )
