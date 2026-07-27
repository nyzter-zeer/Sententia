/**
 * Módulo de traducción usando la API no-oficial de Google Translate (sin API key).
 * Implementa caché para evitar llamadas repetidas.
 */

const CACHE = new Map();
const CACHE_MAX = 500;

const LANG_MAP = {
  'auto': 'auto',
  'ja': 'ja',
  'zh-CN': 'zh-CN',
  'zh-TW': 'zh-TW',
  'en': 'en',
  'es': 'es',
};

/**
 * Traduce un texto usando Google Translate (libre, sin API key).
 * @param {string} text - Texto a traducir
 * @param {string} sourceLang - Idioma origen ('auto', 'ja', 'zh-CN', etc.)
 * @param {string} targetLang - Idioma destino ('es', 'en', etc.)
 * @returns {Promise<string>} Texto traducido
 */
async function translate(text, sourceLang = 'auto', targetLang = 'es') {
  if (!text || !text.trim()) return '';
  
  const key = `${sourceLang}:${targetLang}:${text}`;
  if (CACHE.has(key)) return CACHE.get(key);

  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
    
    const response = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    
    // La respuesta es un array anidado: data[0] = array de segmentos traducidos
    let translated = '';
    if (data && data[0]) {
      translated = data[0]
        .filter(seg => seg && seg[0])
        .map(seg => seg[0])
        .join('');
    }

    if (translated) {
      // Mantener caché limitado
      if (CACHE.size >= CACHE_MAX) {
        const firstKey = CACHE.keys().next().value;
        CACHE.delete(firstKey);
      }
      CACHE.set(key, translated);
    }

    return translated || text;
  } catch (e) {
    console.error('[Translator] Error:', e.message);
    return text;
  }
}

function getCacheSize() {
  return CACHE.size;
}

function clearCache() {
  CACHE.clear();
}

module.exports = { translate, getCacheSize, clearCache };
