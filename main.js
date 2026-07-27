const { app, BrowserWindow, ipcMain, screen, desktopCapturer, dialog, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { createWorker } = require('tesseract.js');

let mainWindow = null;
let overlayWindow = null;
let selectorWindows = [];
let ocrWorker = null;
let currentOcrLangs = '';

// ─── Configuración ────────────────────────────────────────────────────────── //
const CONFIG_PATH = path.join(app.getPath('userData'), 'config.json');
const DEFAULT_CONFIG = {
  sourceLanguage: 'auto',
  targetLanguage: 'es',
  ocrLanguage: 'jpn+chi_sim+eng',
  intervalMs: 1500,
  overlayX: 100,
  overlayY: 100,
  overlayWidth: 680,
  overlayHeight: 160,
  overlayOpacity: 0.92,
  overlayFontSize: 15,
  region: null,
  translationProvider: 'google',
  deeplApiKey: '',
};

function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      return { ...DEFAULT_CONFIG, ...JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8')) };
    }
  } catch (e) { console.error('Config load error:', e); }
  return { ...DEFAULT_CONFIG };
}

function saveConfig(config) {
  try {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf8');
  } catch (e) { console.error('Config save error:', e); }
}

let appConfig = loadConfig();

// ─── Ventana Principal ────────────────────────────────────────────────────── //
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 960,
    height: 700,
    minWidth: 800,
    minHeight: 580,
    backgroundColor: '#0D1117',
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#161B22',
      symbolColor: '#8B949E',
      height: 38,
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    show: true,
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error(`[Main] mainWindow failed to load: ${errorCode} - ${errorDescription} (${validatedURL})`);
  });

  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[Main] mainWindow finished loading');
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Renderer Console] ${message} (Line ${line}: ${sourceId})`);
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
    app.quit();
  });
}

// ─── Ventana Overlay ─────────────────────────────────────────────────────── //
function createOverlayWindow() {
  const { overlayX, overlayY, overlayWidth, overlayHeight, overlayOpacity } = appConfig;

  overlayWindow = new BrowserWindow({
    x: overlayX,
    y: overlayY,
    width: overlayWidth,
    height: overlayHeight,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: true,
    hasShadow: false,
    focusable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  overlayWindow.loadFile(path.join(__dirname, 'overlay', 'overlay.html'));
  overlayWindow.setOpacity(overlayOpacity);
  overlayWindow.setIgnoreMouseEvents(true, { forward: true });
  overlayWindow.setAlwaysOnTop(true, 'screen-saver');
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  let saveTimeout = null;
  const saveOverlayBounds = () => {
    if (!overlayWindow) return;
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      if (!overlayWindow) return;
      const bounds = overlayWindow.getBounds();
      appConfig.overlayX = bounds.x;
      appConfig.overlayY = bounds.y;
      appConfig.overlayWidth = bounds.width;
      appConfig.overlayHeight = bounds.height;
      saveConfig(appConfig);
    }, 500);
  };

  overlayWindow.on('move', saveOverlayBounds);
  overlayWindow.on('resize', saveOverlayBounds);

  overlayWindow.on('closed', () => {
    if (saveTimeout) clearTimeout(saveTimeout);
    overlayWindow = null;
  });
}

// ─── Ventana Selector de Región ──────────────────────────────────────────── //
function createSelectorWindow(display) {
  const { x, y, width, height } = display.bounds;

  const win = new BrowserWindow({
    x, y,
    width, height,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    fullscreen: false,
    movable: false,
    resizable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadFile(path.join(__dirname, 'selector', 'selector.html'));
  win.setIgnoreMouseEvents(false);
  win.focus();

  win.displayId = display.id;
  selectorWindows.push(win);

  win.on('closed', () => {
    selectorWindows = selectorWindows.filter(w => w !== win);
  });
}

function closeSelectorWindows() {
  selectorWindows.forEach(win => {
    if (win && !win.isDestroyed()) {
      win.close();
    }
  });
  selectorWindows = [];
}

// ─── IPC Handlers ────────────────────────────────────────────────────────── //

// Obtener ID de la pantalla para captura por WebRTC
ipcMain.handle('get-screen-source-id', async (_, displayId) => {
  try {
    const displays = screen.getAllDisplays();
    const primaryDisplay = screen.getPrimaryDisplay();
    const targetDisplay = displays.find(d => String(d.id) === String(displayId)) || primaryDisplay;

    const sources = await desktopCapturer.getSources({
      types: ['screen'],
      thumbnailSize: { width: 1, height: 1 } // Muy rápido, sin generar miniaturas reales
    });

    const source = sources.find(s => String(s.display_id) === String(targetDisplay.id)) || sources[0];
    return {
      sourceId: source ? source.id : null,
      width: targetDisplay.bounds.width,
      height: targetDisplay.bounds.height
    };
  } catch (e) {
    console.error('get-screen-source-id error:', e);
    return null;
  }
});

// Configuración
ipcMain.handle('get-config', () => appConfig);
ipcMain.handle('get-version', () => app.getVersion());
ipcMain.handle('save-config', (_, config) => {
  appConfig = { ...appConfig, ...config };
  saveConfig(appConfig);
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('config-changed', appConfig);
  }
  return appConfig;
});

// Overlay: actualizar texto
ipcMain.on('overlay-update-text', (_, text) => {
  if (overlayWindow) {
    overlayWindow.webContents.send('update-text', text);
  }
});

// Overlay: estado (activo/inactivo)
ipcMain.on('overlay-set-status', (_, active) => {
  if (overlayWindow) {
    overlayWindow.webContents.send('set-status', active);
  }
});

// Overlay: mostrar/ocultar
ipcMain.on('overlay-toggle', () => {
  if (!overlayWindow) {
    createOverlayWindow();
  } else if (overlayWindow.isVisible()) {
    overlayWindow.hide();
  } else {
    overlayWindow.show();
  }
});

// Overlay: cambiar opacidad
ipcMain.on('overlay-opacity', (_, val) => {
  if (overlayWindow) overlayWindow.setOpacity(val);
});

// Overlay: mover/redimensionar desde overlay
ipcMain.on('overlay-move', (_, { x, y }) => {
  if (overlayWindow) overlayWindow.setPosition(Math.round(x), Math.round(y));
});

ipcMain.on('overlay-resize', (_, { width, height }) => {
  if (overlayWindow) overlayWindow.setSize(Math.round(width), Math.round(height));
});

// Overlay: click-through on/off
ipcMain.on('overlay-clickthrough', (_, enabled) => {
  if (overlayWindow) {
    overlayWindow.setIgnoreMouseEvents(enabled, { forward: true });
  }
});

// Selector de región
ipcMain.on('open-selector', () => {
  if (mainWindow) mainWindow.minimize();
  
  closeSelectorWindows();

  const displays = screen.getAllDisplays();
  displays.forEach(display => {
    createSelectorWindow(display);
  });
});

ipcMain.on('selector-cancel', () => {
  closeSelectorWindows();
  if (mainWindow) mainWindow.restore();
});

ipcMain.on('selector-done', (event, region) => {
  const senderWindow = BrowserWindow.fromWebContents(event.sender);
  const displayId = senderWindow ? senderWindow.displayId : null;

  closeSelectorWindows();

  if (mainWindow) {
    mainWindow.restore();
    mainWindow.webContents.send('region-selected', { ...region, displayId });
  }
});

// ─── Tesseract OCR Handlers ──────────────────────────────────────────────── //
ipcMain.handle('ocr-init', async (event, langs) => {
  console.log('[Main] ocr-init called for languages:', langs);
  try {
    if (ocrWorker) {
      if (currentOcrLangs === langs) {
        console.log('[Main] OCR already initialized for these languages');
        return { success: true, message: 'OCR already initialized' };
      }
      console.log('[Main] Terminating existing worker...');
      await ocrWorker.terminate();
      ocrWorker = null;
    }

    const cachePath = path.join(app.getPath('userData'), 'tessdata');
    console.log('[Main] Tessdata cache path:', cachePath);
    if (!fs.existsSync(cachePath)) {
      fs.mkdirSync(cachePath, { recursive: true });
    }

    console.log('[Main] Creating Tesseract worker...');
    let lastStatus = '';
    let lastProgressPct = -1;
    
    ocrWorker = await createWorker(langs, 1, {
      cachePath: cachePath,
      logger: (progress) => {
        if (!mainWindow || mainWindow.isDestroyed()) return;

        const status = progress.status;
        const progressPct = Math.round((progress.progress || 0) * 100);

        // Throttling: solo enviar IPC si cambia el estado o si el progreso varía >= 5% en la descarga de modelos
        const isStatusChange = status !== lastStatus;
        const isProgressChange = Math.abs(progressPct - lastProgressPct) >= 5;

        if (isStatusChange || (status === 'loading language traineddata' && isProgressChange)) {
          lastStatus = status;
          lastProgressPct = progressPct;
          mainWindow.webContents.send('ocr-progress', progress);
        }
      }
    });

    console.log('[Main] Tesseract worker created successfully!');
    currentOcrLangs = langs;
    return { success: true };
  } catch (e) {
    console.error('[Main] OCR Init Error in Main Process:', e);
    return { success: false, error: e.message };
  }
});

// OCR a partir de un buffer binario (Uint8Array de la región recortada)
ipcMain.handle('ocr-recognize-buffer', async (_, buffer) => {
  if (!ocrWorker) {
    console.warn('[Main] OCR Worker not initialized!');
    return { error: 'OCR Worker not initialized' };
  }
  try {
    const { data: { text } } = await ocrWorker.recognize(buffer);
    return { text: text.trim() };
  } catch (e) {
    console.error('[Main] OCR Recognize Buffer Error:', e);
    return { error: e.message };
  }
});

// ─── App lifecycle ────────────────────────────────────────────────────────── //
app.whenReady().then(() => {
  createMainWindow();
  createOverlayWindow();
});

app.on('window-all-closed', async () => {
  if (ocrWorker) {
    try {
      await ocrWorker.terminate();
    } catch (e) {
      console.error('Error terminating worker on close:', e);
    }
  }
  app.quit();
});
