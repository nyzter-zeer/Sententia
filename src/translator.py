"""
Motor de traducción con caché y soporte multi-proveedor.
Soporta Google Translate (libre) y DeepL (con API key).
"""

from deep_translator import GoogleTranslator, DeeplTranslator


# Idiomas de destino disponibles
TARGET_LANGUAGES = {
    "Español": "es",
    "Inglés":  "en",
    "Portugués": "pt",
    "Francés": "fr",
}

# Idiomas de origen disponibles
SOURCE_LANGUAGES = {
    "Auto-detect":        "auto",
    "Japonés":            "ja",
    "Chino Simplificado": "zh-CN",
    "Chino Tradicional":  "zh-TW",
    "Inglés":             "en",
}


class TranslationCache:
    """Caché simple en memoria para evitar llamadas API duplicadas."""

    def __init__(self, max_size: int = 500):
        self._cache: dict[str, str] = {}
        self._max_size = max_size

    def get(self, key: str) -> str | None:
        return self._cache.get(key)

    def set(self, key: str, value: str):
        if len(self._cache) >= self._max_size:
            # Eliminar el 20% más antiguo
            items = list(self._cache.keys())
            for k in items[:len(items) // 5]:
                del self._cache[k]
        self._cache[key] = value

    def clear(self):
        self._cache.clear()

    def __len__(self):
        return len(self._cache)


class Translator:
    """
    Motor de traducción con caché.
    Proveedor por defecto: Google Translate (sin API key).
    """

    def __init__(
        self,
        source: str = "auto",
        target: str = "es",
        provider: str = "google",
        deepl_api_key: str = "",
    ):
        self.source = source
        self.target = target
        self.provider = provider
        self.deepl_api_key = deepl_api_key
        self._cache = TranslationCache()

    def translate(self, text: str) -> str:
        """
        Traduce un texto al idioma destino.
        
        Returns:
            Texto traducido o el original si falla.
        """
        if not text or not text.strip():
            return ""

        text = text.strip()
        cache_key = f"{self.source}:{self.target}:{text}"

        # Buscar en caché
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            result = self._do_translate(text)
            if result:
                self._cache.set(cache_key, result)
            return result or text
        except Exception as e:
            print(f"[Traducción] Error: {e}")
            return text  # Retornar original si falla

    def _do_translate(self, text: str) -> str:
        """Realiza la traducción con el proveedor configurado."""
        if self.provider == "deepl" and self.deepl_api_key:
            return self._translate_deepl(text)
        return self._translate_google(text)

    def _translate_google(self, text: str) -> str:
        translator = GoogleTranslator(
            source=self.source,
            target=self.target,
        )
        # Google Translate tiene límite de ~5000 chars por request
        if len(text) > 4500:
            text = text[:4500]
        return translator.translate(text) or ""

    def _translate_deepl(self, text: str) -> str:
        translator = DeeplTranslator(
            api_key=self.deepl_api_key,
            source=self.source if self.source != "auto" else "auto",
            target=self.target,
            use_free_api=True,
        )
        return translator.translate(text) or ""

    def set_languages(self, source: str, target: str):
        """Cambia los idiomas y limpia la caché."""
        if self.source != source or self.target != target:
            self.source = source
            self.target = target
            self._cache.clear()

    def set_provider(self, provider: str, deepl_api_key: str = ""):
        """Cambia el proveedor de traducción."""
        self.provider = provider
        self.deepl_api_key = deepl_api_key
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        return len(self._cache)
