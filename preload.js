const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // Captura WebRTC
  getScreenSourceId: (displayId) => ipcRenderer.invoke('get-screen-source-id', displayId),

  // Config
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  getVersion: () => ipcRenderer.invoke('get-version'),

  // Overlay
  overlayUpdateText: (text) => ipcRenderer.send('overlay-update-text', text),
  overlaySetStatus: (active) => ipcRenderer.send('overlay-set-status', active),
  overlayToggle: () => ipcRenderer.send('overlay-toggle'),
  overlayOpacity: (val) => ipcRenderer.send('overlay-opacity', val),
  overlayMove: (pos) => ipcRenderer.send('overlay-move', pos),
  overlayResize: (size) => ipcRenderer.send('overlay-resize', size),
  overlayClickthrough: (enabled) => ipcRenderer.send('overlay-clickthrough', enabled),

  // Selector
  openSelector: () => ipcRenderer.send('open-selector'),
  selectorCancel: () => ipcRenderer.send('selector-cancel'),
  selectorDone: (region) => ipcRenderer.send('selector-done', region),

  // Listeners (renderer recibe eventos del main)
  onRegionSelected: (cb) => ipcRenderer.on('region-selected', (_, r) => cb(r)),
  onUpdateText: (cb) => ipcRenderer.on('update-text', (_, t) => cb(t)),
  onSetStatus: (cb) => ipcRenderer.on('set-status', (_, s) => cb(s)),
  onConfigChanged: (cb) => ipcRenderer.on('config-changed', (_, cfg) => cb(cfg)),
  
  // OCR IPC
  ocrInit: (langs) => ipcRenderer.invoke('ocr-init', langs),
  ocrRecognizeBuffer: (buffer) => ipcRenderer.invoke('ocr-recognize-buffer', buffer),
  onOcrProgress: (cb) => ipcRenderer.on('ocr-progress', (_, p) => cb(p)),

  // Remover listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
});
