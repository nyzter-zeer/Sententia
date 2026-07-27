"""
Configuración de la aplicación — guardar y cargar desde JSON.
"""

import json
import os
from pathlib import Path


DEFAULT_CONFIG = {
    "source_language": "Auto-detect",
    "target_language": "Español",
    "ocr_language": "Auto (JA+ZH+EN)",
    "translation_provider": "google",
    "deepl_api_key": "",
    "interval_ms": 1500,
    "min_confidence": 0.4,
    "overlay_x": 100,
    "overlay_y": 100,
    "overlay_width": 600,
    "overlay_height": 150,
    "overlay_opacity": 0.85,
    "overlay_font_size": 14,
    "region": None,
    "use_gpu": False,
}

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


class ConfigManager:
    """Gestiona la configuración de la aplicación."""

    def __init__(self):
        self._config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """Carga configuración desde disco."""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge con defaults para manejar nuevas claves
                self._config = {**DEFAULT_CONFIG, **saved}
            except Exception as e:
                print(f"[Config] Error al cargar: {e}")
                self._config = dict(DEFAULT_CONFIG)

    def save(self):
        """Guarda configuración en disco."""
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error al guardar: {e}")

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value

    def update(self, data: dict):
        self._config.update(data)

    def __getitem__(self, key):
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[key] = value
