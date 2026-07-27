"""
Ventana principal de la aplicación.
Usa CustomTkinter para un diseño moderno y oscuro.
"""

import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext

import customtkinter as ctk

from src.capture import ScreenCapture
from src.config_manager import ConfigManager
from src.ocr_engine import OCREngine, LANGUAGE_CONFIGS
from src.overlay import TranslationOverlay
from src.translator import SOURCE_LANGUAGES, TARGET_LANGUAGES, Translator
from src.translation_loop import TranslationLoop
from src.region_selector import RegionSelector


# ── Paleta de colores ─────────────────────────────────────────────────────── #
COLORS = {
    "bg_dark":     "#0D1117",
    "bg_medium":   "#161B22",
    "bg_card":     "#1C2128",
    "border":      "#30363D",
    "accent":      "#2D8CFF",
    "accent_dark": "#1A5FBF",
    "success":     "#39D353",
    "warning":     "#F0A500",
    "danger":      "#F85149",
    "text_primary":  "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted":    "#484F58",
}


class App(ctk.CTk):
    """Ventana principal del traductor de juegos."""

    def __init__(self):
        super().__init__()

        # ── Configuración de CustomTkinter ─────────────────────────────── #
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("🎮 Traductor de Juegos en Tiempo Real")
        self.geometry("900x680")
        self.minsize(800, 600)
        self.configure(fg_color=COLORS["bg_dark"])
        self.resizable(True, True)

        # ── Módulos core ───────────────────────────────────────────────── #
        self._config = ConfigManager()
        self._ocr = OCREngine(
            language_key=self._config.get("ocr_language", "Auto (JA+ZH+EN)"),
            use_gpu=self._config.get("use_gpu", False),
        )
        self._translator = Translator(
            source=SOURCE_LANGUAGES.get(
                self._config.get("source_language", "Auto-detect"), "auto"),
            target=TARGET_LANGUAGES.get(
                self._config.get("target_language", "Español"), "es"),
        )
        self._overlay = TranslationOverlay(self._config)
        self._loop = TranslationLoop(
            ocr=self._ocr,
            translator=self._translator,
            on_translation=self._on_translation,
            on_ocr_text=self._on_ocr_text,
            on_status=self._on_status,
        )

        self._region: dict | None = self._config.get("region")
        self._history: list[dict] = []

        # ── UI ──────────────────────────────────────────────────────────── #
        self._build_ui()
        self._overlay.build(self)

        # ── Cargar OCR ─────────────────────────────────────────────────── #
        self._set_status("⏳ Cargando modelos OCR...", COLORS["warning"])
        self._ocr.load(on_ready=self._on_ocr_ready)

        # Actualizar etiqueta de región si ya existe
        if self._region:
            self._update_region_label()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ================================================================== #
    # Construcción de la UI                                                #
    # ================================================================== #

    def _build_ui(self):
        """Construye todos los componentes de la interfaz."""

        # Grid principal: sidebar | contenido
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_panel()

    # ── Sidebar ────────────────────────────────────────────────────────── #

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=240,
            fg_color=COLORS["bg_medium"],
            corner_radius=0,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(10, weight=1)

        # Logo / título
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=16, pady=(20, 8), sticky="ew")

        ctk.CTkLabel(
            logo_frame,
            text="🎮",
            font=ctk.CTkFont(size=32),
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Traductor\nde Juegos",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"],
            justify="left",
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Tiempo Real • OCR",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Separador
        self._separator(sidebar, row=1)

        # ── Sección: Idiomas ──────────────────────────────────────────── #
        self._section_label(sidebar, "IDIOMAS", row=2)

        lang_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        lang_frame.grid(row=3, column=0, padx=12, pady=4, sticky="ew")
        lang_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            lang_frame,
            text="Idioma origen",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, sticky="w", padx=4)

        self._var_source = ctk.StringVar(
            value=self._config.get("source_language", "Auto-detect"))
        self._combo_source = ctk.CTkComboBox(
            lang_frame,
            values=list(SOURCE_LANGUAGES.keys()),
            variable=self._var_source,
            command=self._on_language_change,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            width=210,
        )
        self._combo_source.grid(row=1, column=0, sticky="ew", padx=4, pady=(2, 8))

        ctk.CTkLabel(
            lang_frame,
            text="Idioma destino",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        ).grid(row=2, column=0, sticky="w", padx=4)

        self._var_target = ctk.StringVar(
            value=self._config.get("target_language", "Español"))
        self._combo_target = ctk.CTkComboBox(
            lang_frame,
            values=list(TARGET_LANGUAGES.keys()),
            variable=self._var_target,
            command=self._on_language_change,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            width=210,
        )
        self._combo_target.grid(row=3, column=0, sticky="ew", padx=4)

        # ── Sección: OCR ─────────────────────────────────────────────── #
        self._separator(sidebar, row=4)
        self._section_label(sidebar, "OCR", row=5)

        ocr_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        ocr_frame.grid(row=6, column=0, padx=12, pady=4, sticky="ew")
        ocr_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            ocr_frame,
            text="Idioma OCR",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, sticky="w", padx=4)

        self._var_ocr_lang = ctk.StringVar(
            value=self._config.get("ocr_language", "Auto (JA+ZH+EN)"))
        self._combo_ocr = ctk.CTkComboBox(
            ocr_frame,
            values=list(LANGUAGE_CONFIGS.keys()),
            variable=self._var_ocr_lang,
            command=self._on_ocr_language_change,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            width=210,
        )
        self._combo_ocr.grid(row=1, column=0, sticky="ew", padx=4, pady=(2, 0))

        # GPU checkbox
        self._var_gpu = ctk.BooleanVar(value=self._config.get("use_gpu", False))
        ctk.CTkCheckBox(
            ocr_frame,
            text="Usar GPU (CUDA)",
            variable=self._var_gpu,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dark"],
        ).grid(row=2, column=0, sticky="w", padx=4, pady=(6, 0))

        # ── Sección: Intervalo ─────────────────────────────────────────── #
        self._separator(sidebar, row=7)
        self._section_label(sidebar, "VELOCIDAD", row=8)

        speed_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        speed_frame.grid(row=9, column=0, padx=12, pady=4, sticky="ew")

        ctk.CTkLabel(
            speed_frame,
            text="Intervalo de captura",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=4)

        self._var_interval = ctk.DoubleVar(
            value=self._config.get("interval_ms", 1500) / 1000)
        self._lbl_interval = ctk.CTkLabel(
            speed_frame,
            text=f"{self._var_interval.get():.1f}s",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["accent"],
        )
        self._lbl_interval.pack(anchor="e", padx=4)

        ctk.CTkSlider(
            speed_frame,
            from_=0.5,
            to=5.0,
            variable=self._var_interval,
            command=self._on_interval_change,
            fg_color=COLORS["border"],
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_dark"],
        ).pack(fill="x", padx=4, pady=(2, 0))

        # ── Filler ─────────────────────────────────────────────────────── #
        ctk.CTkFrame(sidebar, fg_color="transparent").grid(row=10, column=0, sticky="nsew")

        # ── Versión ────────────────────────────────────────────────────── #
        ctk.CTkLabel(
            sidebar,
            text="v1.0.0 • OCR + Translate",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).grid(row=11, column=0, pady=(0, 12))

    # ── Panel principal ────────────────────────────────────────────────── #

    def _build_main_panel(self):
        main = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=0)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # ── Barra de control ─────────────────────────────────────────── #
        control_bar = ctk.CTkFrame(
            main,
            fg_color=COLORS["bg_medium"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        control_bar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        control_bar.grid_columnconfigure(4, weight=1)

        # Botón: Seleccionar región
        self._btn_region = ctk.CTkButton(
            control_bar,
            text="📐  Seleccionar Región",
            command=self._select_region,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            corner_radius=8,
        )
        self._btn_region.grid(row=0, column=0, padx=(12, 4), pady=10)

        # Botón: Iniciar / Pausar
        self._btn_start = ctk.CTkButton(
            control_bar,
            text="▶  Iniciar",
            command=self._toggle_start,
            fg_color=COLORS["success"],
            hover_color="#2EA043",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            corner_radius=8,
            width=120,
        )
        self._btn_start.grid(row=0, column=1, padx=4, pady=10)

        # Botón: Pausar
        self._btn_pause = ctk.CTkButton(
            control_bar,
            text="⏸  Pausar",
            command=self._toggle_pause,
            fg_color=COLORS["warning"],
            hover_color="#C98A00",
            text_color="#000000",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            corner_radius=8,
            width=100,
            state="disabled",
        )
        self._btn_pause.grid(row=0, column=2, padx=4, pady=10)

        # Botón: Overlay
        self._btn_overlay = ctk.CTkButton(
            control_bar,
            text="🪟  Overlay",
            command=self._toggle_overlay,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["accent"],
            text_color=COLORS["accent"],
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            corner_radius=8,
            width=100,
        )
        self._btn_overlay.grid(row=0, column=3, padx=4, pady=10)

        # Botón: Limpiar
        ctk.CTkButton(
            control_bar,
            text="🗑",
            command=self._clear_history,
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=16),
            height=38,
            width=38,
            corner_radius=8,
        ).grid(row=0, column=5, padx=(0, 12), pady=10)

        # Etiqueta de región
        self._lbl_region = ctk.CTkLabel(
            control_bar,
            text="Sin región seleccionada",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        )
        self._lbl_region.grid(row=0, column=4, padx=8, pady=10, sticky="ew")

        # ── Panel de texto ───────────────────────────────────────────── #
        text_frame = ctk.CTkFrame(
            main,
            fg_color=COLORS["bg_medium"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        text_frame.grid(row=1, column=0, padx=16, pady=4, sticky="ew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_columnconfigure(1, weight=1)

        # OCR (texto original)
        ocr_col = ctk.CTkFrame(text_frame, fg_color="transparent")
        ocr_col.grid(row=0, column=0, padx=12, pady=12, sticky="ew")
        ocr_col.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            ocr_col,
            text="TEXTO DETECTADO (OCR)",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"],
        ).grid(row=0, column=0, sticky="w")

        self._txt_ocr = ctk.CTkTextbox(
            ocr_col,
            height=90,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=12),
            corner_radius=8,
        )
        self._txt_ocr.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        # Traducción
        trans_col = ctk.CTkFrame(text_frame, fg_color="transparent")
        trans_col.grid(row=0, column=1, padx=12, pady=12, sticky="ew")
        trans_col.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            trans_col,
            text="TRADUCCIÓN",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"],
        ).grid(row=0, column=0, sticky="w")

        self._txt_translation = ctk.CTkTextbox(
            trans_col,
            height=90,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["accent"],
            border_width=1,
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
        )
        self._txt_translation.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        # ── Historial ───────────────────────────────────────────────── #
        hist_frame = ctk.CTkFrame(
            main,
            fg_color=COLORS["bg_medium"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        hist_frame.grid(row=2, column=0, padx=16, pady=(4, 8), sticky="nsew")
        hist_frame.grid_columnconfigure(0, weight=1)
        hist_frame.grid_rowconfigure(1, weight=1)

        hist_header = ctk.CTkFrame(hist_frame, fg_color="transparent")
        hist_header.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="ew")
        hist_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hist_header,
            text="HISTORIAL DE TRADUCCIONES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"],
        ).grid(row=0, column=0, sticky="w")

        self._txt_history = ctk.CTkTextbox(
            hist_frame,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=12, family="Consolas"),
            corner_radius=8,
        )
        self._txt_history.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        # ── Barra de estado ──────────────────────────────────────────── #
        status_bar = ctk.CTkFrame(
            main,
            fg_color=COLORS["bg_medium"],
            height=32,
            corner_radius=0,
        )
        status_bar.grid(row=3, column=0, sticky="ew", padx=0)
        status_bar.grid_propagate(False)

        self._lbl_status = ctk.CTkLabel(
            status_bar,
            text="● Listo",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        )
        self._lbl_status.pack(side="left", padx=12)

        self._lbl_cache = ctk.CTkLabel(
            status_bar,
            text="Caché: 0",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        )
        self._lbl_cache.pack(side="right", padx=12)

    # ── Helpers de UI ─────────────────────────────────────────────────── #

    def _separator(self, parent, row: int):
        ctk.CTkFrame(
            parent,
            height=1,
            fg_color=COLORS["border"],
            corner_radius=0,
        ).grid(row=row, column=0, padx=12, pady=6, sticky="ew")

    def _section_label(self, parent, text: str, row: int):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"],
        ).grid(row=row, column=0, padx=16, pady=(4, 2), sticky="w")

    # ================================================================== #
    # Callbacks y lógica de negocio                                        #
    # ================================================================== #

    def _on_ocr_ready(self, success: bool):
        """Llamado cuando el OCR termina de cargar."""
        self.after(0, lambda: self._handle_ocr_ready(success))

    def _handle_ocr_ready(self, success: bool):
        if success:
            self._set_status("✅ OCR listo", COLORS["success"])
            self._btn_start.configure(state="normal")
        else:
            self._set_status("❌ Error al cargar OCR", COLORS["danger"])

    def _on_translation(self, text: str):
        """Actualiza la UI con una nueva traducción."""
        self.after(0, lambda: self._update_translation(text))

    def _update_translation(self, text: str):
        # Panel de traducción
        self._txt_translation.delete("1.0", "end")
        self._txt_translation.insert("1.0", text)

        # Overlay
        self._overlay.update_text(text)
        self._overlay.set_status(True)

        # Historial
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {text}\n{'─' * 50}\n"
        self._txt_history.insert("end", entry)
        self._txt_history.see("end")
        self._history.append({"time": ts, "text": text})

        # Actualizar caché counter
        self._lbl_cache.configure(
            text=f"Caché: {self._translator.cache_size}")

    def _on_ocr_text(self, text: str):
        """Actualiza el panel de texto OCR."""
        self.after(0, lambda: self._update_ocr_panel(text))

    def _update_ocr_panel(self, text: str):
        self._txt_ocr.delete("1.0", "end")
        self._txt_ocr.insert("1.0", text)

    def _on_status(self, msg: str):
        """Actualiza la barra de estado."""
        self.after(0, lambda: self._set_status(msg))

    def _set_status(self, msg: str, color: str = None):
        color = color or COLORS["text_secondary"]
        self._lbl_status.configure(text=f"● {msg}", text_color=color)

    # ── Región ────────────────────────────────────────────────────────── #

    def _select_region(self):
        """Abre el selector de región."""
        # Ocultar ventana principal temporalmente
        self.iconify()
        self.after(300, self._open_region_selector)

    def _open_region_selector(self):
        def on_select(region):
            self._region = region
            self._loop.set_region(region)
            self._config.set("region", region)
            self._config.save()
            self.after(0, self._update_region_label)
            self.deiconify()

        t = threading.Thread(
            target=lambda: RegionSelector(on_select).start(),
            daemon=True,
        )
        t.start()
        # Restaurar ventana si el selector se cancela
        self.after(500, self._ensure_visible)

    def _ensure_visible(self):
        """Verifica que la ventana principal sea visible."""
        if self.state() == "iconic":
            self.deiconify()

    def _update_region_label(self):
        if self._region:
            r = self._region
            self._lbl_region.configure(
                text=f"📐 {r['width']}×{r['height']}  en  ({r['left']}, {r['top']})",
                text_color=COLORS["success"],
            )

    # ── Traducción ────────────────────────────────────────────────────── #

    def _toggle_start(self):
        if not self._loop.is_running:
            if not self._region:
                messagebox.showwarning(
                    "Sin región",
                    "Primero selecciona una región de la pantalla con '📐 Seleccionar Región'",
                )
                return
            self._loop.set_interval(self._var_interval.get())
            self._loop.start()
            self._btn_start.configure(
                text="⏹  Detener",
                fg_color=COLORS["danger"],
                hover_color="#B91C1C",
            )
            self._btn_pause.configure(state="normal")
            self._overlay.set_status(True)
        else:
            self._loop.stop()
            self._btn_start.configure(
                text="▶  Iniciar",
                fg_color=COLORS["success"],
                hover_color="#2EA043",
            )
            self._btn_pause.configure(state="disabled", text="⏸  Pausar")
            self._overlay.set_status(False)

    def _toggle_pause(self):
        self._loop.toggle_pause()
        if self._loop.is_paused:
            self._btn_pause.configure(text="▶  Reanudar")
            self._overlay.set_status(False)
        else:
            self._btn_pause.configure(text="⏸  Pausar")
            self._overlay.set_status(True)

    def _toggle_overlay(self):
        self._overlay.toggle()
        state = "visible" if self._overlay.is_visible else "oculto"
        self._set_status(f"Overlay {state}")

    def _clear_history(self):
        self._txt_history.delete("1.0", "end")
        self._history.clear()

    # ── Cambios de configuración ──────────────────────────────────────── #

    def _on_language_change(self, _=None):
        src_key = self._var_source.get()
        tgt_key = self._var_target.get()
        src_code = SOURCE_LANGUAGES.get(src_key, "auto")
        tgt_code = TARGET_LANGUAGES.get(tgt_key, "es")
        self._translator.set_languages(src_code, tgt_code)
        self._config.update({
            "source_language": src_key,
            "target_language": tgt_key,
        })
        self._config.save()

    def _on_ocr_language_change(self, _=None):
        lang_key = self._var_ocr_lang.get()
        self._config.set("ocr_language", lang_key)
        self._config.save()
        self._set_status("⏳ Recargando OCR...", COLORS["warning"])
        self._ocr.change_language(lang_key, on_ready=self._on_ocr_ready)

    def _on_interval_change(self, value):
        v = float(value)
        self._lbl_interval.configure(text=f"{v:.1f}s")
        self._loop.set_interval(v)
        self._config.set("interval_ms", int(v * 1000))

    # ── Cierre ────────────────────────────────────────────────────────── #

    def _on_close(self):
        self._loop.stop()
        self._config.save()
        self.destroy()
