/**
 * app.js — Lógica del renderer principal
 * Maneja OCR (Tesseract.js), traducción y control del loop
 */

// ─── Estado ─────────────────────────────────────────────────────────────── //
const state = {
  config: null,
  region: null,
  running: false,
  paused: false,
  loopTimer: null,
  lastRawText: '',
  captureCount: 0,
  ocrReady: false,
  worker: null,
  localStream: null,
  captureVideo: null,
  streamBounds: { width: window.screen.width, height: window.screen.height },
};

// Caché de traducciones en el renderer
const translationCache = new Map();

// ─── Referencias DOM ─────────────────────────────────────────────────────── //
const $ = id => document.getElementById(id);

const els = {
  selSource:    $('sel-source'),
  selTarget:    $('sel-target'),
  selOcrLang:   $('sel-ocr-lang'),
  selProvider:  $('sel-provider'),
  inputDeeplKey: $('input-deepl-key'),
  deeplConfig:  $('deepl-config'),
  sliderInterval: $('slider-interval'),
  intervalVal:  $('interval-val'),
  sliderOpacity: $('slider-opacity'),
  opacityVal:   $('opacity-val'),
  sliderFontsize: $('slider-fontsize'),
  fontsizeVal:  $('fontsize-val'),
  btnRegion:    $('btn-region'),
  btnStart:     $('btn-start'),
  btnPause:     $('btn-pause'),
  btnOverlay:   $('btn-overlay'),
  btnClear:     $('btn-clear'),
  btnCopy:      $('btn-copy'),
  regionLabel:  $('region-label'),
  ocrText:      $('ocr-text'),
  translatedText: $('translated-text'),
  historyList:  $('history-list'),
  statusText:   $('status-text'),
  statusDot:    $('status-indicator').querySelector('.status-dot'),
  ocrDot:       $('ocr-dot'),
  ocrStatusText: $('ocr-status-text'),
  cacheInfo:    $('cache-info'),
  framesCount:  $('frames-count'),
  badgeLang:    $('badge-lang'),
};

// ─── Init ─────────────────────────────────────────────────────────────────── //
async function init() {
  // Cargar config
  state.config = await window.api.getConfig();
  applyConfig(state.config);

  // Mostrar versión de la app
  try {
    const version = await window.api.getVersion();
    const verSpan = $('app-version');
    if (verSpan) verSpan.textContent = `v${version}`;
  } catch (err) {
    console.error('Error al cargar la versión:', err);
  }

  // Escuchar región seleccionada
  window.api.onRegionSelected(async (region) => {
    state.region = region;
    updateRegionLabel(region);
    setStatus('Región seleccionada — listo para iniciar', 'idle');
    // Guardar la región seleccionada para que persista
    saveConfigDebounced({ region });

    // Si estaba corriendo, reiniciamos el stream para la nueva región/pantalla
    if (state.running && !state.paused) {
      try {
        stopLoop();
        await startCaptureStream(region.displayId);
        startLoop();
      } catch (err) {
        console.error('Error al reiniciar stream tras cambiar región:', err);
      }
    }
  });

  // Eventos de controles
  bindControls();

  // Escuchar progreso del OCR desde el proceso principal
  window.api.onOcrProgress(m => {
    if (m.status === 'loading tesseract core') {
      setOcrStatus('loading', 'Cargando motor OCR...');
    } else if (m.status === 'initializing tesseract') {
      setOcrStatus('loading', 'Inicializando Tesseract...');
    } else if (m.status === 'loading language traineddata') {
      const pct = Math.round((m.progress || 0) * 100);
      setOcrStatus('loading', `Descargando modelos de idioma... ${pct}%`);
    } else if (m.status === 'initialized api') {
      setOcrStatus('ready', '✅ OCR listo');
      state.ocrReady = true;
    }
  });

  // Iniciar Tesseract en el Main Process
  await initOCR(state.config.ocrLanguage || 'jpn+chi_sim+eng');
}

// ─── OCR con Tesseract.js ────────────────────────────────────────────────── //
async function initOCR(langs) {
  setOcrStatus('loading', `Cargando OCR (${langs})...`);
  state.ocrReady = false;

  try {
    const res = await window.api.ocrInit(langs);
    if (res.success) {
      setOcrStatus('ready', '✅ OCR listo');
      state.ocrReady = true;
    } else {
      setOcrStatus('error', `❌ Error: ${res.error}`);
    }
  } catch (err) {
    console.error('OCR init error:', err);
    setOcrStatus('error', '❌ Error al cargar OCR');
  }
}

// ─── Traducción ──────────────────────────────────────────────────────────── //
async function translateText(text) {
  const provider = els.selProvider.value;
  const src = els.selSource.value;
  const tgt = els.selTarget.value;
  const key = `${provider}:${src}:${tgt}:${text}`;

  if (translationCache.has(key)) {
    updateCacheInfo();
    return translationCache.get(key);
  }

  try {
    let translated = '';
    if (provider === 'deepl') {
      const apiKey = els.inputDeeplKey.value.trim();
      if (!apiKey) {
        return '⚠️ Configura tu DeepL API Key';
      }

      const isFree = apiKey.endsWith(':fx');
      const baseUrl = isFree ? 'https://api-free.deepl.com/v2/translate' : 'https://api.deepl.com/v2/translate';

      let targetLang = tgt.toUpperCase();
      if (targetLang === 'EN') targetLang = 'EN-US';
      if (targetLang === 'PT') targetLang = 'PT-BR';

      let sourceLang = undefined;
      if (src !== 'auto') {
        sourceLang = src.toUpperCase();
        if (sourceLang === 'ZH-CN' || sourceLang === 'ZH-TW') {
          sourceLang = 'ZH';
        }
      }

      const bodyData = {
        text: [text],
        target_lang: targetLang
      };
      if (sourceLang) {
        bodyData.source_lang = sourceLang;
      }

      const resp = await fetch(baseUrl, {
        method: 'POST',
        headers: {
          'Authorization': `DeepL-Auth-Key ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(bodyData)
      });

      if (!resp.ok) {
        throw new Error(`DeepL API Error: HTTP ${resp.status}`);
      }

      const data = await resp.json();
      translated = data.translations?.[0]?.text || text;
    } else {
      const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${src}&tl=${tgt}&dt=t&q=${encodeURIComponent(text)}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      translated = data[0]?.filter(s => s?.[0]).map(s => s[0]).join('') || text;
    }

    if (translationCache.size >= 500) {
      translationCache.delete(translationCache.keys().next().value);
    }
    translationCache.set(key, translated);
    updateCacheInfo();
    return translated;
  } catch (e) {
    console.error('Translation error:', e);
    return text;
  }
}

// ─── Control de Stream WebRTC de Captura ──────────────────────────────────── //
async function startCaptureStream(displayId) {
  if (state.localStream) {
    stopCaptureStream();
  }

  try {
    const res = await window.api.getScreenSourceId(displayId);
    if (!res || !res.sourceId) {
      throw new Error('No se encontró el ID de captura para la pantalla.');
    }

    state.streamBounds = { width: res.width, height: res.height };

    state.localStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        mandatory: {
          chromeMediaSource: 'desktop',
          chromeMediaSourceId: res.sourceId,
          minWidth: 1280,
          maxWidth: 4096,
          minHeight: 720,
          maxHeight: 2160
        }
      }
    });

    state.captureVideo = document.createElement('video');
    state.captureVideo.srcObject = state.localStream;
    state.captureVideo.muted = true;
    state.captureVideo.playsInline = true;
    await new Promise((resolve) => {
      state.captureVideo.onloadedmetadata = () => {
        state.captureVideo.play().then(resolve);
      };
    });
  } catch (err) {
    console.error('Error al iniciar stream de captura:', err);
    throw err;
  }
}

function stopCaptureStream() {
  if (state.localStream) {
    state.localStream.getTracks().forEach(track => track.stop());
    state.localStream = null;
  }
  if (state.captureVideo) {
    state.captureVideo.pause();
    state.captureVideo.srcObject = null;
    state.captureVideo = null;
  }
}

async function getRegionBuffer(region) {
  if (!state.captureVideo || state.captureVideo.paused) return null;

  const displayWidth = region.screenWidth || state.streamBounds.width;
  const displayHeight = region.screenHeight || state.streamBounds.height;

  const scaleX = state.captureVideo.videoWidth / displayWidth;
  const scaleY = state.captureVideo.videoHeight / displayHeight;

  const cropX = region.x * scaleX;
  const cropY = region.y * scaleY;
  const cropW = region.width * scaleX;
  const cropH = region.height * scaleY;

  const canvas = document.createElement('canvas');
  canvas.width = Math.round(cropW);
  canvas.height = Math.round(cropH);

  const ctx = canvas.getContext('2d');
  ctx.drawImage(state.captureVideo, cropX, cropY, cropW, cropH, 0, 0, canvas.width, canvas.height);

  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
  if (!blob) return null;

  const arrayBuffer = await blob.arrayBuffer();
  return new Uint8Array(arrayBuffer);
}

// ─── Loop principal ──────────────────────────────────────────────────────── //
async function runLoop() {
  if (!state.running || state.paused) return;
  if (!state.region) return;
  if (!state.ocrReady) {
    setStatus('⏳ Esperando OCR...', 'idle');
    return;
  }

  try {
    // 1. Obtener buffer de la región capturada de forma local vía WebRTC
    const buffer = await getRegionBuffer(state.region);
    if (!buffer) {
      return;
    }

    // 2. Hacer OCR en el proceso principal usando el buffer binario
    const res = await window.api.ocrRecognizeBuffer(buffer);
    
    if (res.error) {
      console.error('OCR Loop Error:', res.error);
      setStatus(`⚠ Error: ${res.error}`, 'idle');
      return;
    }

    state.captureCount++;
    els.framesCount.textContent = `${state.captureCount} capturas`;

    const rawText = res.text;

    if (rawText && rawText !== state.lastRawText) {
      state.lastRawText = rawText;

      // Mostrar texto OCR
      els.ocrText.textContent = rawText;

      // Detectar idioma para badge
      const srcLang = els.selSource.options[els.selSource.selectedIndex].text;
      els.badgeLang.textContent = srcLang;

      // 3. Traducir
      const translated = await translateText(rawText);

      if (translated) {
        // Actualizar UI
        els.translatedText.textContent = translated;

        // Overlay
        window.api.overlayUpdateText(translated);
        window.api.overlaySetStatus(true);

        // Historial
        addToHistory(rawText, translated);

        setStatus('▶ Traduciendo...', 'active');
      }
    }
  } catch (e) {
    console.error('Loop error:', e);
    setStatus(`⚠ Error: ${e.message}`, 'idle');
  }
}

function startLoop() {
  const intervalMs = parseInt(els.sliderInterval.value, 10);
  state.loopTimer = setInterval(runLoop, intervalMs);
}

function stopLoop() {
  if (state.loopTimer) {
    clearInterval(state.loopTimer);
    state.loopTimer = null;
  }
}

// ─── Controles ───────────────────────────────────────────────────────────── //
function bindControls() {
  // Región
  els.btnRegion.addEventListener('click', () => {
    window.api.openSelector();
  });

  // Iniciar / Detener
  els.btnStart.addEventListener('click', async () => {
    if (!state.running) {
      if (!state.region) {
        showToast('Primero selecciona una región con 📐');
        return;
      }
      if (!state.ocrReady) {
        showToast('El OCR todavía se está cargando...');
        return;
      }
      
      try {
        setStatus('⏳ Iniciando captura...', 'idle');
        await startCaptureStream(state.region.displayId);
        state.running = true;
        state.paused = false;
        startLoop();
        els.btnStart.className = 'btn btn-danger';
        els.btnStart.innerHTML = '<span class="btn-icon">⏹</span><span>Detener</span>';
        els.btnPause.disabled = false;
        setStatus('▶ Traducción en curso', 'active');
        window.api.overlaySetStatus(true);
      } catch (err) {
        showToast('Error al iniciar la captura de pantalla');
        setStatus('❌ Error al iniciar captura', 'idle');
      }
    } else {
      state.running = false;
      state.paused = false;
      stopLoop();
      stopCaptureStream();
      els.btnStart.className = 'btn btn-success';
      els.btnStart.innerHTML = '<span class="btn-icon">▶</span><span>Iniciar</span>';
      els.btnPause.disabled = true;
      els.btnPause.innerHTML = '<span class="btn-icon">⏸</span><span>Pausar</span>';
      setStatus('⏹ Detenido', 'idle');
      window.api.overlaySetStatus(false);
    }
  });

  // Pausar
  els.btnPause.addEventListener('click', async () => {
    state.paused = !state.paused;
    if (state.paused) {
      stopLoop();
      stopCaptureStream();
      els.btnPause.innerHTML = '<span class="btn-icon">▶</span><span>Reanudar</span>';
      setStatus('⏸ Pausado', 'idle');
      window.api.overlaySetStatus(false);
    } else {
      try {
        setStatus('⏳ Reanudando captura...', 'idle');
        await startCaptureStream(state.region.displayId);
        startLoop();
        els.btnPause.innerHTML = '<span class="btn-icon">⏸</span><span>Pausar</span>';
        setStatus('▶ Reanudado', 'active');
        window.api.overlaySetStatus(true);
      } catch (err) {
        showToast('Error al reanudar la captura de pantalla');
        state.paused = true;
        setStatus('❌ Error al reanudar', 'idle');
      }
    }
  });

  // Overlay toggle
  els.btnOverlay.addEventListener('click', () => window.api.overlayToggle());

  // Limpiar historial
  els.btnClear.addEventListener('click', () => {
    els.historyList.innerHTML = '<div class="history-empty">Historial limpiado</div>';
    translationCache.clear();
    updateCacheInfo();
  });

  // Copiar traducción
  els.btnCopy.addEventListener('click', () => {
    const text = els.translatedText.textContent;
    if (text && !text.includes('aparecerá aquí')) {
      navigator.clipboard.writeText(text).then(() => showToast('¡Copiado!'));
    }
  });

  // Sliders
  els.sliderInterval.addEventListener('input', e => {
    const val = parseInt(e.target.value);
    els.intervalVal.textContent = `${(val / 1000).toFixed(1)}s`;
    if (state.running && !state.paused) {
      stopLoop();
      startLoop();
    }
    saveConfigDebounced({ intervalMs: val });
  });

  els.sliderOpacity.addEventListener('input', e => {
    const val = parseInt(e.target.value);
    els.opacityVal.textContent = `${val}%`;
    window.api.overlayOpacity(val / 100);
    saveConfigDebounced({ overlayOpacity: val / 100 });
  });

  els.sliderFontsize.addEventListener('input', e => {
    const val = parseInt(e.target.value);
    els.fontsizeVal.textContent = `${val}px`;
    saveConfigDebounced({ overlayFontSize: val });
    // Enviar al overlay
    window.api.overlayUpdateText(state.lastRawText ? els.translatedText.textContent : '');
  });

  // Idiomas
  els.selSource.addEventListener('change', () => saveConfigDebounced({ sourceLanguage: els.selSource.value }));
  els.selTarget.addEventListener('change', () => {
    translationCache.clear();
    updateCacheInfo();
    saveConfigDebounced({ targetLanguage: els.selTarget.value });
  });

  // Proveedor de traducción
  els.selProvider.addEventListener('change', () => {
    const val = els.selProvider.value;
    toggleDeeplConfigVisibility(val);
    translationCache.clear();
    updateCacheInfo();
    saveConfigDebounced({ translationProvider: val });
  });

  els.inputDeeplKey.addEventListener('input', () => {
    const val = els.inputDeeplKey.value.trim();
    translationCache.clear();
    updateCacheInfo();
    saveConfigDebounced({ deeplApiKey: val });
  });

  // OCR lang
  els.selOcrLang.addEventListener('change', async () => {
    const lang = els.selOcrLang.value;
    state.ocrReady = false;
    state.lastRawText = '';
    saveConfigDebounced({ ocrLanguage: lang });
    await initOCR(lang);
  });
}

// ─── Helpers ─────────────────────────────────────────────────────────────── //
function applyConfig(cfg) {
  if (!cfg) return;
  els.selSource.value = cfg.sourceLanguage || 'auto';
  els.selTarget.value = cfg.targetLanguage || 'es';
  els.selOcrLang.value = cfg.ocrLanguage || 'jpn+chi_sim+eng';
  els.selProvider.value = cfg.translationProvider || 'google';
  els.inputDeeplKey.value = cfg.deeplApiKey || '';
  toggleDeeplConfigVisibility(cfg.translationProvider || 'google');

  els.sliderInterval.value = cfg.intervalMs || 1500;
  els.intervalVal.textContent = `${((cfg.intervalMs || 1500) / 1000).toFixed(1)}s`;
  els.sliderOpacity.value = Math.round((cfg.overlayOpacity || 0.92) * 100);
  els.opacityVal.textContent = `${Math.round((cfg.overlayOpacity || 0.92) * 100)}%`;
  els.sliderFontsize.value = cfg.overlayFontSize || 15;
  els.fontsizeVal.textContent = `${cfg.overlayFontSize || 15}px`;

  if (cfg.region) {
    state.region = cfg.region;
    updateRegionLabel(cfg.region);
  }
}

function toggleDeeplConfigVisibility(provider) {
  if (provider === 'deepl') {
    els.deeplConfig.style.display = 'block';
  } else {
    els.deeplConfig.style.display = 'none';
  }
}

function updateRegionLabel(region) {
  els.regionLabel.textContent = `📐 ${region.width}×${region.height}  en  (${region.x}, ${region.y})`;
  els.regionLabel.classList.add('has-region');
}

function setStatus(msg, type = 'idle') {
  els.statusText.textContent = msg;
  els.statusDot.className = `status-dot status-dot--${type}`;
}

function setOcrStatus(type, msg) {
  els.ocrDot.className = `status-dot status-dot--${type}`;
  els.ocrStatusText.textContent = msg;
}

function addToHistory(raw, translated) {
  // Quitar el placeholder si existe
  const empty = els.historyList.querySelector('.history-empty');
  if (empty) empty.remove();

  const time = new Date().toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const item = document.createElement('div');
  item.className = 'history-item';
  item.innerHTML = `
    <span class="history-time">${time}</span>
    <span class="history-text">${translated}</span>
  `;
  els.historyList.appendChild(item);
  els.historyList.scrollTop = els.historyList.scrollHeight;
}

function updateCacheInfo() {
  els.cacheInfo.textContent = `Caché: ${translationCache.size} frases`;
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%);
    background: #1C2128; border: 1px solid #30363D; color: #E6EDF3;
    padding: 8px 18px; border-radius: 8px; font-size: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5); z-index: 9999;
    animation: slideIn 0.2s ease;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2200);
}

// Debounce para no guardar config en cada pixel del slider
let saveTimer = null;
function saveConfigDebounced(patch) {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    window.api.saveConfig(patch);
  }, 600);
}

// ─── Arrancar ─────────────────────────────────────────────────────────────── //
window.addEventListener('DOMContentLoaded', () => init());
