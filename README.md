# Sententia v1.3.0

> **Sententia** is a high-performance desktop application designed to translate games and apps in real-time using OCR (Optical Character Recognition).
>
> **Sententia** es una aplicación de escritorio de alto rendimiento diseñada para traducir juegos y aplicaciones en tiempo real mediante OCR (Reconocimiento Óptico de Caracteres).

---

### 📥 Downloads & Releases / Descargas y Lanzamientos
* 🚀 **[Latest Release (v1.3.0) / Última Versión (v1.3.0)](https://github.com/nyzter-zeer/Sententia/releases/latest)**
  * **Installer / Instalador (`.exe`)**: Standard setup wizard for Windows / Asistente de instalación estándar para Windows.
  * **Portable Executable / Ejecutable Portable (`.exe`)**: Run directly without installation / Ejecutable independiente listo para usar sin instalar.

---

[English](#english) | [Español](#español)

---

# English

## 🚀 Key Features

* **Real-time Capture**: Monitors and extracts text from a pre-defined screen region at configurable intervals (from ultra-fast `0.5s` up to `5.0s`).
* **Smart Region Selector**: Full multi-monitor support. When selecting a region, the main window minimizes automatically and overlays an interactive transparent canvas across all active screens.
* **Transparent Floating Overlay**: A borderless window that stays on top of your games (perfect for *Borderless Windowed* mode). It features:
  * Real-time opacity control (from `20%` to `100%`).
  * Customizable font size (from `10px` to `28px`).
  * Interactive mode to move/resize, or *click-through* mode (ignores mouse interaction) to prevent interfering with gameplay.
* **Caching & Network Optimization**: Features a local cache of up to 500 recent translations to prevent redundant API queries and optimize bandwidth.
* **Interactive History**: Integrated panel displaying the translation log of the current session, making it easy to review quick-passing text or dialogues.
* **Multi-language Support**:
  * **Source language (OCR)**: Japanese, Simplified Chinese, Traditional Chinese, English, and a mixed auto-detection mode (`JA+ZH+EN`).
  * **Target language**: Spanish, English, Portuguese, and French.
* **Multiple Translation Providers**:
  * **Google Translate (Free)**: Built-in, free integration requiring no API Key.
  * **DeepL API**: Native integration with support for both free (`:fx`) and pro API keys.

---

## 🛠️ Architecture & Tech Stack

The project is designed under a modern hybrid architecture that decouples rendering from heavy processing:

| Component / Layer | Technology Used | Function and Details |
| :--- | :--- | :--- |
| **Container / Runtime** | [Electron.js](https://www.electronjs.org/) | Runs the desktop shell, merging Node.js for system operations and Chromium for the UI. |
| **OCR Engine** | [Tesseract.js](https://tesseract.projectnaptha.com/) v5 | Spawns and manages workers in Electron's main process, downloading and caching language models (`tessdata`) locally in the user data directory to avoid blocking the UI. |
| **Screen Capture** | WebRTC & `desktopCapturer` API | Natively grabs screen video streams without using external binaries, achieving high efficiency. |
| **Region Crop** | HTML5 Canvas API | Maps selection coordinates, scales proportions relative to actual screen resolution, and exports a raw binary PNG buffer (`Uint8Array`) directly to the OCR worker. |
| **Translation Engine** | Fetch API + gtx Endpoint / DeepL API | Asynchronously requests translations. Redundant queries are filtered in-memory via the local cache. |
| **Styling & Design** | CSS3 & Google Fonts | High-quality dark UI using custom typefaces (`Inter` and `JetBrains Mono`) with smooth color transitions. |

---

## 📁 Directory Structure

The project is modularized to ensure easy maintenance and scalability:

```
Sententia/
├── main.js              # Electron main process (window lifecycle, IPC, and OCR init)
├── preload.js           # Secure context bridge exporting system bindings to the renderer
├── package.json         # Project setup, dependencies, and build configurations
├── instalar.bat         # Automated Node.js and dependencies installer script for Windows
├── iniciar.bat          # Quick-run script for the development environment
├── compilar.bat         # Compiling execution launcher
├── compilar.ps1         # Advanced PowerShell script to bundle the app portably
├── renderer/            # Main Dashboard Window
│   ├── index.html       # Control panel HTML layout
│   ├── style.css        # Premium dark styling sheets
│   └── app.js           # UI interaction controller, WebRTC stream, and translation loop
├── overlay/             # Transparent Overlay Window
│   ├── overlay.html     # Floating overlay view
│   └── overlay.js/css   # Floating text styles and window interactions
├── selector/            # Region Selection Canvas
│   ├── selector.html    # Fullscreen selection canvas
│   └── selector.js/css  # Handle drag & draw capture boxes
├── lang-data/           # Bundled resource assets
├── assets/              # Graphics and icons
└── src/                 # [LEGACY] Original Python Prototype
    ├── main.py          # Python Tkinter entry point
    ├── requirements.txt # Python requirements (easyocr, OpenCV, customtkinter, etc.)
    └── app/capture/etc. # Internal Python logic for OCR, translation, and local capture
```

---

## ⚡ Installation & Quick Start on Windows

No development tools setup is required to get started on Windows.

### Step 1: Install Dependencies
Double-click the **`instalar.bat`** file.
* *How it works:*
  1. Checks if Node.js is already installed.
  2. If missing, it downloads Node.js LTS via PowerShell.
  3. Executes a silent, unattended installation of Node.js.
  4. Automatically refreshes PATH variables.
  5. Runs `npm install` to load Electron, Tesseract.js, and other dependencies.

### Step 2: Launch the App
Double-click the **`iniciar.bat`** file.
* *How it works:*
  Runs `npm start` to fire up the Electron desktop container.

---

## ⚙️ How to Use the Translator

1. **Configure your game**: Run the game in **Windowed** or **Borderless Windowed** mode. (Note: The overlay cannot draw over exclusive fullscreen games).
2. **Select Area**: Click **📐 Seleccionar Región**. The main control panel will minimize, and a selection canvas will appear. Drag a box over the text/subtitles box of your game.
3. **Configure Languages**: On the left sidebar:
   * Select your game's language (*Source Language*).
   * Select your preferred translation language (*Target Language*).
4. **Start translating**: Click the green **▶ Iniciar** button.
5. **Position the Overlay**: Click **🪟 Overlay** to open the translation container, position/resize it, and adjust its opacity and font size in the dashboard settings.

> [!NOTE]
> **First Run**: The first time you select a new OCR language, Tesseract.js downloads its language data file (~10MB to 40MB). This happens only once and caches local files permanently.

---

## 📦 Compiling and Bundling the Executable (`.exe`)

To package a standalone executable distribution that does not require Node.js on the target machine:

1. Double-click the **`compilar.bat`** file.
2. The PowerShell script **`compilar.ps1`** runs:
   * **Portable Mode**: If Node.js is missing from your global path, the script downloads Node.js portable (ZIP), extracts it to `node_portable/`, and targets it locally. This keeps your operating system completely clean!
   * **Dependency Bundling**: Automatically installs build requirements.
   * **Build**: Runs `electron-builder` to package the files.
3. Once completed (takes ~3 to 5 minutes), the build folder **`dist/`** opens automatically.
4. You will find:
   * A standard Windows installer.
   * A standalone, single-file **portable `.exe`** (~80MB+).

---

## 🐍 Alternative Python Prototype (Legacy)

For developers preferring **Python** to web languages (JS/Chromium), the `src/` directory contains the legacy desktop client prototype built with:
* **UI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for dark mode window components.
* **Capture**: `mss` library for high-speed frame grabbing.
* **OCR**: [EasyOCR](https://github.com/JaidedAI/EasyOCR) and `OpenCV` for image processing.
* **Translation**: `deep-translator` multi-engine routing.

To run:
1. Install Python 3.10+.
2. Install requirements: `pip install -r requirements.txt`
3. Execute: `python main.py`

---

# Español

## 🚀 Características Clave

* **Captura en Tiempo Real**: Monitoriza y extrae texto de una región de pantalla predefinida a intervalos configurables (desde el más rápido de `0.5s` hasta `5.0s`).
* **Selector de Región Inteligente**: Diseñado para soportar múltiples monitores. Al activar la selección, la ventana principal de la aplicación se minimiza automáticamente y despliega un lienzo de selección interactivo y transparente en todas tus pantallas.
* **Overlay Flotante y Transparente**: Una ventana flotante sin bordes que se coloca por encima de tus juegos (ideal para el modo *Borderless Windowed*). Ofrece:
  * Control de opacidad en tiempo real (de `20%` a `100%`).
  * Tamaño de fuente personalizable (de `10px` a `28px`).
  * Modo interactivo para mover/redimensionar o modo *click-through* (ignorar ratón) para no interferir con el juego.
* **Caché y Optimización de Ancho de Banda**: Cuenta con un sistema de caché de hasta 500 traducciones recientes para evitar consultas duplicadas y optimizar el consumo de red.
* **Historial Interactivo**: Panel integrado con el registro completo de traducciones de la sesión, facilitando volver a leer diálogos o textos que pasaron rápido en pantalla.
* **Soporte Multiidioma**:
  * **Idiomas de entrada (OCR)**: Japonés, Chino Simplificado, Chino Tradicional, Inglés y un modo de detección automática mixta (`JA+ZH+EN`).
  * **Idiomas de destino**: Español, Inglés, Portugués y Francés.
* **Múltiples Proveedores de Traducción**:
  * **Google Translate (Libre)**: Integración integrada y gratuita que no requiere ninguna clave de API.
  * **DeepL API**: Conexión nativa con soporte para claves gratuitas (`:fx`) y de pago (Pro).

---

## 🛠️ Arquitectura y Stack Tecnológico

El proyecto está diseñado bajo una arquitectura híbrida moderna que separa el renderizado de la interfaz del motor de procesamiento pesado:

| Componente / Capa | Tecnología Utilizada | Función y Detalles |
| :--- | :--- | :--- |
| **Contenedor / Runtime** | [Electron.js](https://www.electronjs.org/) | Ejecuta la aplicación de escritorio combinando Node.js para operaciones del sistema y Chromium para la UI. |
| **Motor de OCR** | [Tesseract.js](https://tesseract.projectnaptha.com/) v5 | Inicializa y ejecuta trabajadores (*workers*) en el proceso principal de Electron, descargando localmente los modelos de idioma (`tessdata`) en la carpeta de datos de usuario para evitar bloquear la interfaz de usuario. |
| **Captura de Pantalla** | WebRTC & API `desktopCapturer` | Accede de forma nativa a la señal de video de las pantallas del sistema sin usar ejecutables externos, logrando un rendimiento extremadamente rápido y eficiente. |
| **Procesamiento de Región** | HTML5 Canvas API | Mapea las coordenadas físicas de la región seleccionada, escala las proporciones respecto a la resolución real y extrae un búfer de imagen en PNG binario (`Uint8Array`) para alimentar directamente al OCR. |
| **Motor de Traducción** | Fetch API + Endpoint gtx / DeepL API | Consume de manera asíncrona los traductores. Las solicitudes fallidas o repetidas son filtradas previamente por la memoria caché interna del renderizador. |
| **Diseño y Estilos** | CSS3 & Google Fonts | Interfaz gráfica oscura premium utilizando fuentes personalizadas como `Inter` y `JetBrains Mono` con transiciones de color fluidas. |

---

## 📁 Estructura del Directorio

El proyecto se divide de manera modular facilitando su mantenimiento y escalabilidad:

```
Sententia/
├── main.js              # Proceso principal de Electron (configuración de ventanas, IPC y OCR)
├── preload.js           # Puente seguro (Context Bridge) que expone funciones del sistema al frontend
├── package.json         # Configuración del proyecto, dependencias y scripts de construcción
├── instalar.bat         # Instalador automatizado de Node.js y dependencias para Windows
├── iniciar.bat          # Script de ejecución rápida en entorno de desarrollo
├── compilar.bat         # Script iniciador del proceso de compilación
├── compilar.ps1         # Script avanzado en PowerShell para empaquetar de forma portable
├── renderer/            # Ventana Principal (Dashboard)
│   ├── index.html       # Estructura del panel de control
│   ├── style.css        # Hoja de estilos con diseño oscuro y moderno
│   └── app.js           # Controlador principal de la UI, captura WebRTC y loop de traducción
├── overlay/             # Ventana de Traducción Flotante
│   ├── overlay.html     # Vista transparente flotante
│   └── overlay.js/css   # Estilo y comportamiento del texto flotante en pantalla
├── selector/            # Ventana de Selección de Área
│   ├── selector.html    # Lienzo a pantalla completa para el selector
│   └── selector.js/css  # Manejo del dibujo del rectángulo de recorte (drag & drop)
├── lang-data/           # Recursos adicionales del empaquetado
├── assets/              # Recursos gráficos del proyecto (íconos, etc.)
└── src/                 # [LEGADO] Prototipo original desarrollado en Python
    ├── main.py          # Punto de entrada de la versión Python (Tkinter)
    ├── requirements.txt # Dependencias requeridas por el prototipo Python (easyocr, OpenCV, etc.)
    └── app/capture/etc. # Módulos internos en Python para OCR, traducción y captura local
```

---

## ⚡ Instalación y Uso Rápido en Windows

La aplicación está diseñada para que cualquier usuario de Windows pueda ponerla en marcha en menos de 2 minutos sin configurar herramientas de desarrollo previas.

### Paso 1: Instalar Dependencias
Haz doble clic sobre el archivo **`instalar.bat`**.
* *¿Qué hace internamente?*
  1. Verifica si tienes Node.js instalado.
  2. Si no lo encuentra, utiliza PowerShell de forma segura para descargar el instalador oficial de Node.js LTS.
  3. Realiza una instalación desatendida y silenciosa de Node.js en tu sistema.
  4. Actualiza automáticamente las variables de entorno de tu terminal.
  5. Ejecuta `npm install` para instalar Tesseract, Electron y las dependencias del proyecto.

### Paso 2: Iniciar la Aplicación
Haz doble clic sobre el archivo **`iniciar.bat`**.
* *¿Qué hace internamente?*
  Inicia el entorno de desarrollo ejecutando `npm start`, lo que despliega el panel de control y el overlay de traducción.

---

## ⚙️ Guía de Uso del Traductor

1. **Prepara tu juego**: Ejecútalo preferentemente en modo **Ventana** o **Ventana sin Bordes (Borderless Windowed)**. (Nota: El overlay flotante no se superpondrá sobre juegos en pantalla completa exclusiva).
2. **Selecciona el Área**: Haz clic en el botón **📐 Seleccionar Región**. Tu ventana principal se minimizará y podrás dibujar un rectángulo con el ratón directamente sobre la zona de la pantalla donde aparecen los subtítulos o textos del juego.
3. **Ajusta los Idiomas**: En el panel izquierdo de la ventana principal:
   * Define el idioma de entrada en el que está tu juego (por ejemplo, *Japonés*).
   * Elige tu idioma preferido para la traducción (por ejemplo, *Español*).
4. **Inicia el Traductor**: Haz clic en el botón verde **▶ Iniciar**.
5. **Ajusta el Overlay**: Haz clic en **🪟 Overlay** para mostrar el cuadro transparente. Arrástralo a cualquier posición conveniente de tu pantalla. Si lo deseas, puedes ajustar la opacidad del fondo y el tamaño de la letra en los controles de la ventana principal.

> [!NOTE]
> **Primera Ejecución**: La primera vez que selecciones un idioma para el OCR, Tesseract.js descargará un archivo de datos de entrenamiento del idioma (~10MB a 40MB). Esto ocurre una única vez por idioma y se guarda permanentemente en la caché local del disco duro.

---

## 📦 Compilación y Generación del Ejecutable (`.exe`)

Si quieres compartir la aplicación con alguien que no sea desarrollador o simplemente deseas tener un archivo portable ejecutable independiente en tu PC sin necesidad de tener Node.js instalado globalmente:

1. Haz doble clic sobre el archivo **`compilar.bat`**.
2. Se iniciará el script automatizado **`compilar.ps1`** en PowerShell:
   * **Entorno Portable**: Si no tienes Node.js en tu sistema, el script descargará una versión portable (ZIP) de Node.js LTS, la extraerá localmente en la carpeta `node_portable/` y configurará un entorno aislado temporal. ¡Esto asegura que no se instale ni ensucie nada globalmente en tu máquina!
   * **Instalación y Descarga**: Descarga localmente las herramientas de empaquetado de Electron.
   * **Construcción**: Invoca a `electron-builder` para compilar el código.
3. Una vez finalizado el proceso (suele tardar de 3 a 5 minutos), el script abrirá automáticamente la carpeta **`dist/`** en el explorador de archivos.
4. Encontrarás dos versiones listas para usar:
   * Un instalador tradicional de Windows.
   * Un archivo ejecutable `.exe` **totalmente portable** e independiente de más de 80MB.

---

## 🐍 Prototipo Alternativo en Python (Histórico / Desarrollo)

Para aquellos desarrolladores que prefieran trabajar con **Python** en lugar de tecnologías web (JavaScript/HTML/Electron), la carpeta `src/` contiene la primera versión funcional de Sententia construida con la siguiente arquitectura:
* **UI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) para interfaces nativas oscuras.
* **Captura**: Biblioteca `mss` para capturas de pantalla ultra rápidas.
* **OCR**: [EasyOCR](https://github.com/JaidedAI/EasyOCR) y `OpenCV` para procesamiento de imágenes.
* **Traducción**: `deep-translator` para conexión multi-motor.

Para ejecutar la versión de Python:
1. Asegúrate de tener Python 3.10+ instalado.
2. Instala los requerimientos: `pip install -r requirements.txt`
3. Ejecuta la aplicación: `python main.py`
