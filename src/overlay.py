"""
Overlay flotante y transparente para mostrar la traducción sobre el juego.
Click-through: los clics pasan al juego debajo.
"""

import tkinter as tk
import threading


class TranslationOverlay:
    """
    Ventana overlay sin bordes, siempre encima, semi-transparente.
    Usa win32 para hacer click-through en Windows.
    """

    # Color de fondo clave para transparencia
    TRANSPARENT_KEY = "#010101"

    def __init__(self, config):
        self._config = config
        self._root: tk.Tk | None = None
        self._label: tk.Label | None = None
        self._canvas: tk.Canvas | None = None
        self._visible = False
        self._dragging = False
        self._drag_x = 0
        self._drag_y = 0
        self._current_text = ""
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Construcción de la ventana                                           #
    # ------------------------------------------------------------------ #

    def build(self, master_root: tk.Tk):
        """Construye el overlay como Toplevel sobre la ventana principal."""
        self._root = tk.Toplevel(master_root)
        self._root.overrideredirect(True)  # Sin bordes / barra de título
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", self._config.get("overlay_opacity", 0.85))
        self._root.configure(bg=self.TRANSPARENT_KEY)
        self._root.attributes("-transparentcolor", self.TRANSPARENT_KEY)

        x = self._config.get("overlay_x", 100)
        y = self._config.get("overlay_y", 100)
        w = self._config.get("overlay_width", 600)
        h = self._config.get("overlay_height", 150)
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        self._build_content()
        self._bind_events()
        self._apply_click_through()
        self._visible = True

    def _build_content(self):
        """Construye el contenido visual del overlay."""
        # Fondo redondeado con canvas
        w = self._config.get("overlay_width", 600)
        h = self._config.get("overlay_height", 150)

        self._canvas = tk.Canvas(
            self._root,
            width=w,
            height=h,
            bg=self.TRANSPARENT_KEY,
            highlightthickness=0,
        )
        self._canvas.pack(fill="both", expand=True)

        # Fondo oscuro semi-transparente (rectángulo redondeado simulado)
        pad = 8
        self._bg_rect = self._canvas.create_rectangle(
            pad, pad, w - pad, h - pad,
            fill="#0D1117",
            outline="#30363D",
            width=1,
        )

        # Barra superior de arrastre
        self._canvas.create_rectangle(
            pad, pad, w - pad, pad + 22,
            fill="#161B22",
            outline="",
        )

        # Indicador de color (punto de estado)
        self._status_dot = self._canvas.create_oval(
            pad + 10, pad + 6, pad + 20, pad + 16,
            fill="#39D353",
            outline="",
        )

        # Etiqueta "TRADUCCIÓN EN VIVO"
        self._canvas.create_text(
            pad + 32, pad + 11,
            text="TRADUCCIÓN EN VIVO",
            fill="#8B949E",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )

        # Botón minimizar (×)
        self._close_btn = self._canvas.create_text(
            w - pad - 8, pad + 11,
            text="×",
            fill="#8B949E",
            font=("Segoe UI", 12, "bold"),
            anchor="e",
            tags="close_btn",
        )

        # Texto de traducción principal
        font_size = self._config.get("overlay_font_size", 14)
        self._text_id = self._canvas.create_text(
            w // 2, (h + 30) // 2,
            text="Selecciona una región para empezar...",
            fill="#E6EDF3",
            font=("Segoe UI", font_size),
            width=w - pad * 4,
            justify="center",
            anchor="center",
        )

    def _bind_events(self):
        """Vincula eventos de arrastre y cierre."""
        # Arrastre desde la barra superior
        self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_motion)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._canvas.tag_bind("close_btn", "<ButtonPress-1>", lambda e: self.hide())

    def _apply_click_through(self):
        """Aplica click-through en Windows usando pywin32."""
        try:
            import win32gui
            import win32con
            hwnd = self._root.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        except ImportError:
            print("[Overlay] pywin32 no encontrado — click-through no disponible.")
        except Exception as e:
            print(f"[Overlay] Error en click-through: {e}")

    # ------------------------------------------------------------------ #
    # Actualización del texto                                              #
    # ------------------------------------------------------------------ #

    def update_text(self, text: str):
        """Actualiza el texto del overlay (thread-safe)."""
        with self._lock:
            self._current_text = text
        if self._root:
            self._root.after(0, self._refresh_text)

    def _refresh_text(self):
        with self._lock:
            text = self._current_text
        if self._canvas and self._text_id:
            self._canvas.itemconfig(self._text_id, text=text)

    def set_status(self, active: bool):
        """Cambia el color del punto de estado."""
        if self._canvas and self._status_dot:
            color = "#39D353" if active else "#F85149"
            self._root.after(0, lambda: self._canvas.itemconfig(
                self._status_dot, fill=color))

    # ------------------------------------------------------------------ #
    # Arrastre                                                             #
    # ------------------------------------------------------------------ #

    def _on_drag_start(self, event):
        self._drag_x = event.x_root - self._root.winfo_x()
        self._drag_y = event.y_root - self._root.winfo_y()
        self._dragging = True

    def _on_drag_motion(self, event):
        if self._dragging:
            x = event.x_root - self._drag_x
            y = event.y_root - self._drag_y
            self._root.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event):
        self._dragging = False
        # Guardar posición
        self._config.set("overlay_x", self._root.winfo_x())
        self._config.set("overlay_y", self._root.winfo_y())

    # ------------------------------------------------------------------ #
    # Visibilidad y configuración                                          #
    # ------------------------------------------------------------------ #

    def show(self):
        if self._root:
            self._root.deiconify()
            self._visible = True

    def hide(self):
        if self._root:
            self._root.withdraw()
            self._visible = False

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def set_opacity(self, value: float):
        """Cambia la opacidad del overlay (0.1 - 1.0)."""
        if self._root:
            self._root.attributes("-alpha", max(0.1, min(1.0, value)))

    def resize(self, width: int, height: int):
        """Redimensiona el overlay."""
        if self._root:
            x = self._root.winfo_x()
            y = self._root.winfo_y()
            self._root.geometry(f"{width}x{height}+{x}+{y}")

    def set_font_size(self, size: int):
        """Cambia el tamaño de fuente del texto traducido."""
        if self._canvas and self._text_id:
            self._canvas.itemconfig(
                self._text_id,
                font=("Segoe UI", size)
            )

    @property
    def is_visible(self) -> bool:
        return self._visible
