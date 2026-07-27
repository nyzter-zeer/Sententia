"""
Selector de región interactivo.
Permite al usuario arrastrar un rectángulo en la pantalla para
definir el área de captura (ROI - Region of Interest).
"""

import tkinter as tk
from typing import Callable


class RegionSelector:
    """
    Abre una ventana transparente de pantalla completa que permite
    seleccionar una región arrastrando el ratón.
    """

    def __init__(self, on_select: Callable[[dict], None]):
        """
        Args:
            on_select: Callback llamado con dict {left, top, width, height}
                       cuando el usuario termina la selección.
        """
        self._on_select = on_select
        self._start_x = 0
        self._start_y = 0
        self._rect = None
        self._root = None
        self._canvas = None

    def start(self):
        """Inicia el selector en la pantalla principal."""
        self._root = tk.Tk()
        self._root.withdraw()

        # Ventana de selección
        self._sel_win = tk.Toplevel(self._root)
        self._sel_win.attributes("-fullscreen", True)
        self._sel_win.attributes("-topmost", True)
        self._sel_win.attributes("-alpha", 0.25)
        self._sel_win.configure(bg="black")
        self._sel_win.config(cursor="crosshair")

        # Canvas sobre toda la pantalla
        w = self._sel_win.winfo_screenwidth()
        h = self._sel_win.winfo_screenheight()
        self._canvas = tk.Canvas(
            self._sel_win,
            width=w,
            height=h,
            bg="black",
            highlightthickness=0,
            cursor="crosshair",
        )
        self._canvas.pack(fill="both", expand=True)

        # Instrucción
        self._canvas.create_text(
            w // 2, 40,
            text="Arrastra para seleccionar la región de texto  •  ESC para cancelar",
            fill="white",
            font=("Segoe UI", 16, "bold"),
        )

        # Bindings
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._sel_win.bind("<Escape>", self._on_cancel)

        self._root.mainloop()

    def _on_press(self, event):
        self._start_x = event.x
        self._start_y = event.y
        if self._rect:
            self._canvas.delete(self._rect)

    def _on_drag(self, event):
        if self._rect:
            self._canvas.delete(self._rect)
        self._rect = self._canvas.create_rectangle(
            self._start_x, self._start_y, event.x, event.y,
            outline="#00D4FF",
            width=2,
            fill="#00D4FF",
            stipple="gray25",
        )

    def _on_release(self, event):
        x1 = min(self._start_x, event.x)
        y1 = min(self._start_y, event.y)
        x2 = max(self._start_x, event.x)
        y2 = max(self._start_y, event.y)

        w = x2 - x1
        h = y2 - y1

        self._close()

        if w > 10 and h > 10:
            region = {"left": x1, "top": y1, "width": w, "height": h}
            self._on_select(region)

    def _on_cancel(self, event=None):
        self._close()

    def _close(self):
        try:
            self._root.quit()
            self._root.destroy()
        except Exception:
            pass
