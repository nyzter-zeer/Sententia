# Traductor de Juegos en Tiempo Real

Aplicación de escritorio **sin necesidad de instalar Python** para traducir juegos en tiempo real mediante OCR.

Creado por **[nyzter-zeer](https://github.com/nyzter-zeer)**

## ⚡ Instalación rápida (3 pasos)

### 1. Instalar todo automáticamente
```
Doble clic en: instalar.bat
```
> Descarga e instala Node.js automáticamente si no lo tienes, y luego instala todas las dependencias.

### 2. Iniciar la app para probarla
```
Doble clic en: iniciar.bat
```

### 3. (Opcional) Compilar un .exe standalone
```
Doble clic en: compilar.bat
```
> Genera un instalador de Windows (`.exe`) en la carpeta `dist/` que puedes distribuir sin necesitar Node.js.

---

## Uso

1. **Abre tu juego** en modo ventana o sin bordes (Borderless Windowed)
2. Haz clic en **📐 Seleccionar Región** y arrastra sobre el cuadro de diálogo del juego
3. Elige el idioma OCR en el panel izquierdo
4. Haz clic en **▶ Iniciar**
5. La traducción aparece en el **overlay flotante** encima del juego

---

## Idiomas soportados

| Idioma origen | OCR recomendado |
|---|---|
| Japonés | `Japonés` |
| Chino Simplificado | `Chino Simplificado` |
| Chino Tradicional | `Chino Tradicional` |
| Inglés | `Inglés` |
| Mezcla | `Auto (JA+ZH+EN)` |

**Idioma destino:** Español (por defecto), también Inglés, Portugués, Francés.

---

## Tecnología

| Componente | Tecnología |
|---|---|
| App | Electron (Node.js) |
| OCR | Tesseract.js v5 |
| Traducción | Google Translate (sin API key) |
| Captura | Electron desktopCapturer |

---

## Estructura
```
├── main.js            # Proceso principal Electron
├── preload.js         # Puente IPC seguro
├── renderer/          # UI principal (HTML/CSS/JS)
├── overlay/           # Ventana overlay transparente
├── selector/          # Selector de región
├── src/               # Módulos auxiliares
├── assets/            # Íconos
├── instalar.bat       # Instalador automático
├── iniciar.bat        # Iniciar app
└── compilar.bat       # Compilar .exe standalone
```

## Notas

- **Primera vez**: Tesseract.js descarga los modelos de idioma (~10-40MB). Solo ocurre una vez y se guardan en caché.
- **Conexión a internet**: Necesaria para descargar modelos la primera vez y para la traducción (Google Translate).
- **Juego en modo ventana**: El overlay solo funciona bien en modo ventana o borderless; no en pantalla completa exclusiva.
