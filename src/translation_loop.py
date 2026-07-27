"""
Loop principal de traducción en tiempo real.
Corre en un hilo separado para no bloquear la UI.
"""

import threading
import time
import numpy as np

from src.capture import ScreenCapture
from src.ocr_engine import OCREngine
from src.translator import Translator


class TranslationLoop:
    """
    Captura → OCR → Traducción en hilo de fondo.
    Llama callbacks cuando hay nuevo texto o traducción disponible.
    """

    def __init__(
        self,
        ocr: OCREngine,
        translator: Translator,
        on_translation=None,
        on_ocr_text=None,
        on_status=None,
    ):
        self._ocr = ocr
        self._translator = translator
        self._capture = ScreenCapture()

        self._on_translation = on_translation  # callback(translated: str)
        self._on_ocr_text = on_ocr_text        # callback(raw: str)
        self._on_status = on_status            # callback(msg: str)

        self._region: dict | None = None
        self._interval: float = 1.5  # segundos entre capturas
        self._running = False
        self._paused = False
        self._thread: threading.Thread | None = None
        self._last_raw_text = ""

    # ------------------------------------------------------------------ #
    # Control                                                              #
    # ------------------------------------------------------------------ #

    def start(self):
        if self._running:
            return
        self._running = True
        self._paused = False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._emit_status("▶ Traducción iniciada")

    def stop(self):
        self._running = False
        self._paused = False
        self._emit_status("⏹ Traducción detenida")

    def pause(self):
        self._paused = True
        self._emit_status("⏸ Pausado")

    def resume(self):
        self._paused = False
        self._emit_status("▶ Reanudado")

    def toggle_pause(self):
        if self._paused:
            self.resume()
        else:
            self.pause()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    # ------------------------------------------------------------------ #
    # Configuración                                                        #
    # ------------------------------------------------------------------ #

    def set_region(self, region: dict | None):
        self._region = region

    def set_interval(self, seconds: float):
        self._interval = max(0.3, seconds)

    # ------------------------------------------------------------------ #
    # Loop interno                                                         #
    # ------------------------------------------------------------------ #

    def _loop(self):
        while self._running:
            if self._paused or self._region is None:
                time.sleep(0.1)
                continue

            if not self._ocr.is_ready:
                self._emit_status("⏳ Cargando modelos OCR...")
                time.sleep(0.5)
                continue

            try:
                # 1. Capturar
                frame = self._capture.capture(self._region)
                if frame is None:
                    time.sleep(self._interval)
                    continue

                # 2. OCR
                raw_text = self._ocr.extract_text(frame)

                # 3. ¿Cambió el texto?
                if raw_text and raw_text != self._last_raw_text:
                    self._last_raw_text = raw_text
                    if self._on_ocr_text:
                        self._on_ocr_text(raw_text)

                    # 4. Traducir
                    translated = self._translator.translate(raw_text)
                    if self._on_translation and translated:
                        self._on_translation(translated)

            except Exception as e:
                self._emit_status(f"⚠ Error: {e}")

            time.sleep(self._interval)

    def _emit_status(self, msg: str):
        if self._on_status:
            self._on_status(msg)
        print(f"[Loop] {msg}")
