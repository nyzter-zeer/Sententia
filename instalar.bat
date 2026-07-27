@echo off
setlocal EnableDelayedExpansion
title Instalador - Traductor de Juegos en Tiempo Real
color 0A

echo.
echo  ============================================================
echo    TRADUCTOR DE JUEGOS EN TIEMPO REAL
echo    Instalador automatico - Sin necesidad de Python
echo  ============================================================
echo.

REM ─── Verificar si Node.js ya esta instalado ─────────────────────
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Node.js ya esta instalado:
    node --version
    goto :instalar_deps
)

echo  [1/3] Node.js no encontrado. Descargando instalador...
echo.

REM ─── Descargar Node.js LTS ──────────────────────────────────────
set NODE_URL=https://nodejs.org/dist/v20.15.0/node-v20.15.0-x64.msi
set NODE_MSI=%TEMP%\node-installer.msi

powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%NODE_MSI%' }"

if not exist "%NODE_MSI%" (
    echo.
    echo  [ERROR] No se pudo descargar Node.js
    echo  Por favor, descargalo manualmente desde: https://nodejs.org
    echo  (Elige la version LTS e instala)
    echo  Luego vuelve a ejecutar este archivo.
    pause
    exit /b 1
)

echo  [2/3] Instalando Node.js silenciosamente...
msiexec /i "%NODE_MSI%" /quiet /norestart ADDLOCAL=ALL

REM Esperar que termine y refrescar PATH
timeout /t 5 /nobreak >nul
del "%NODE_MSI%" >nul 2>&1

REM Refrescar variables de entorno
call refreshenv >nul 2>&1

REM Agregar Node.js al PATH de esta sesion manualmente si es necesario
set "NODE_PATH=C:\Program Files\nodejs"
if exist "%NODE_PATH%\node.exe" (
    set "PATH=%NODE_PATH%;%PATH%"
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [NOTA] Node.js fue instalado pero requiere reiniciar el terminal.
    echo  Por favor cierra esta ventana, abre una nueva y ejecuta instalar.bat de nuevo.
    pause
    exit /b 0
)

echo  [OK] Node.js instalado correctamente: 
node --version

:instalar_deps
echo.
echo  [3/3] Instalando dependencias de la aplicacion...
echo  (Esto puede tardar 1-3 minutos la primera vez)
echo.

call npm install --progress=false

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Fallo la instalacion de dependencias.
    echo  Verifica tu conexion a internet e intenta de nuevo.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   Instalacion completada exitosamente!
echo.
echo   Para INICIAR la aplicacion:
echo     - Doble clic en  iniciar.bat
echo.
echo   Para COMPILAR un .exe standalone:
echo     - Doble clic en  compilar.bat
echo  ============================================================
echo.
pause
