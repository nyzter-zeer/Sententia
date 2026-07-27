"""
Módulo de captura de pantalla usando mss.
Captura una región específica de la pantalla de forma eficiente.
"""

import mss
import numpy as np
from PIL import Image


class ScreenCapture:
    """Captura regiones de pantalla de forma eficiente usando mss."""

    def __init__(self):
        self._sct = None

    def _get_sct(self):
        """Obtiene o crea una instancia de mss (thread-safe)."""
        if self._sct is None:
            self._sct = mss.mss()
        return self._sct

    def capture(self, region: dict) -> np.ndarray | None:
        """
        Captura una región de la pantalla.
        
        Args:
            region: Diccionario con keys 'left', 'top', 'width', 'height'
        
        Returns:
            Array numpy BGR o None si falla
        """
        if not region or region.get('width', 0) <= 0 or region.get('height', 0) <= 0:
            return None

        try:
            sct = self._get_sct()
            monitor = {
                "left": region["left"],
                "top": region["top"],
                "width": region["width"],
                "height": region["height"],
            }
            screenshot = sct.grab(monitor)
            # Convertir de BGRA a RGB para EasyOCR / PIL
            img = np.array(screenshot)
            img = img[:, :, :3]  # Quitar canal alpha
            return img
        except Exception as e:
            print(f"[Captura] Error: {e}")
            return None

    def capture_as_pil(self, region: dict) -> Image.Image | None:
        """Captura y retorna una imagen PIL."""
        arr = self.capture(region)
        if arr is None:
            return None
        return Image.fromarray(arr)

    def get_monitors(self) -> list[dict]:
        """Retorna información de todos los monitores disponibles."""
        sct = self._get_sct()
        return [dict(m) for m in sct.monitors[1:]]  # [0] es el monitor virtual completo

    def close(self):
        """Libera recursos."""
        if self._sct:
            self._sct.close()
            self._sct = None
