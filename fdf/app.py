"""Графический интерфейс на tkinter.

Единственный модуль, который импортирует графическую библиотеку.
"""

import tkinter as tk

from fdf.model import Map
from fdf.projection import Camera, segments

BACKGROUND = "#000000"
HUD_COLOR = "#A0A0A0"


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
        self.canvas.bind("<Configure>", self._on_resize)

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
            10, 10, anchor=tk.NW, fill=HUD_COLOR, font=("TkDefaultFont", 10), text="Esc — выход"
        )
