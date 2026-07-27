"""
Motor OCR basado en EasyOCR.
Soporta Japonés, Chino Simplificado, Chino Tradicional e Inglés.
"""

import threading
import numpy as np
import easyocr


# Mapa de idiomas disponibles en esta app
LANGUAGE_CONFIGS = {
    "Japonés":            ["ja", "en"],
    "Chino Simplificado": ["ch_sim", "en"],
    "Chino Tradicional":  ["ch_tra", "en"],
    "Inglés":             ["en"],
    "Auto (JA+ZH+EN)":   ["ja", "ch_sim", "en"],
}


class OCREngine:
    """Wrapper sobre EasyOCR con soporte multi-idioma."""

    def __init__(self, language_key: str = "Auto (JA+ZH+EN)", use_gpu: bool = False):
        self._reader = None
        self._language_key = language_key
        self._use_gpu = use_gpu
        self._lock = threading.Lock()
        self._loading = False
        self._loaded = False
        self._on_ready_cb = None

    # ------------------------------------------------------------------ #
    # Carga del modelo (puede tomar tiempo / descargar modelos)            #
    # ------------------------------------------------------------------ #

    def load(self, on_ready=None):
        """Carga el lector EasyOCR en un hilo aparte para no bloquear la UI."""
        self._on_ready_cb = on_ready
        self._loading = True
        t = threading.Thread(target=self._load_worker, daemon=True)
        t.start()

    def _load_worker(self):
        try:
            langs = LANGUAGE_CONFIGS.get(self._language_key, ["ja", "ch_sim", "en"])
            print(f"[OCR] Cargando modelos para: {langs}")
            self._reader = easyocr.Reader(
                langs,
                gpu=self._use_gpu,
                verbose=False,
                download_enabled=True,
            )
            self._loaded = True
            print("[OCR] Modelos cargados correctamente.")
        except Exception as e:
            print(f"[OCR] Error al cargar modelos: {e}")
            self._loaded = False
        finally:
            self._loading = False
            if self._on_ready_cb:
                self._on_ready_cb(self._loaded)

    # ------------------------------------------------------------------ #
    # Extracción de texto                                                  #
    # ------------------------------------------------------------------ #

    def extract_text(self, image: np.ndarray, min_confidence: float = 0.3) -> str:
        """
        Extrae texto de una imagen numpy.
        
        Args:
            image: Array numpy RGB
            min_confidence: Confianza mínima para incluir un resultado
        
        Returns:
            Texto extraído como string (líneas unidas con espacio)
        """
        if not self._loaded or self._reader is None:
            return ""
        if image is None or image.size == 0:
            return ""

        with self._lock:
            try:
                results = self._reader.readtext(
                    image,
                    detail=1,
                    paragraph=True,
                    batch_size=4,
                )
                texts = [
                    r[1] for r in results
                    if len(r) >= 3 and r[2] >= min_confidence
                ]
                return " ".join(texts).strip()
            except Exception as e:
                print(f"[OCR] Error al extraer texto: {e}")
                return ""

    # ------------------------------------------------------------------ #
    # Estado                                                               #
    # ------------------------------------------------------------------ #

    @property
    def is_loading(self) -> bool:
        return self._loading

    @property
    def is_ready(self) -> bool:
        return self._loaded

    def change_language(self, language_key: str, on_ready=None):
        """Cambia el idioma y recarga el lector."""
        if language_key == self._language_key and self._loaded:
            return
        self._language_key = language_key
        self._loaded = False
        self._reader = None
        self.load(on_ready=on_ready)
