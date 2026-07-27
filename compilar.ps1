# ============================================================
#  COMPILADOR - Traductor de Juegos en Tiempo Real
#  Descarga Node.js portable, instala deps y genera el .exe
# ============================================================

$Host.UI.RawUI.WindowTitle = "Compilando Traductor de Juegos..."

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   TRADUCTOR DE JUEGOS - Generando .exe standalone" -ForegroundColor Cyan
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NodeDir    = Join-Path $ProjectDir "node_portable"
$NodeExe    = Join-Path $NodeDir "node.exe"
$NpmScript  = Join-Path $NodeDir "node_modules\npm\bin\npm-cli.js"

# ── Paso 1: Verificar si node ya está en PATH ───────────────────────
$NodeBin = $null
try { $NodeBin = (Get-Command node -ErrorAction Stop).Source } catch {}

if ($NodeBin) {
    Write-Host "  [OK] Node.js encontrado en PATH" -ForegroundColor Green
    $UseGlobal = $true
} elseif (Test-Path $NodeExe) {
    Write-Host "  [OK] Node.js portable encontrado" -ForegroundColor Green
    $UseGlobal = $false
} else {
    # ── Descargar Node.js portable (ZIP) ─────────────────────────────
    Write-Host "  [1/4] Descargando Node.js LTS portable..." -ForegroundColor Yellow
    Write-Host "        (No queda instalado en el sistema)" -ForegroundColor Gray

    $NodeVersion = "v20.15.0"
    $NodeZipUrl  = "https://nodejs.org/dist/$NodeVersion/node-$NodeVersion-win-x64.zip"
    $NodeZipPath = Join-Path $env:TEMP "node-portable.zip"

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $ProgressPreference = 'SilentlyContinue'

    try {
        Invoke-WebRequest -Uri $NodeZipUrl -OutFile $NodeZipPath -UseBasicParsing
        Write-Host "  [OK] Node.js descargado." -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] No se pudo descargar Node.js: $_" -ForegroundColor Red
        Read-Host "`n  Presiona Enter para salir"
        exit 1
    }

    # ── Extraer ZIP ───────────────────────────────────────────────────
    Write-Host "  [2/4] Extrayendo Node.js..." -ForegroundColor Yellow

    if (Test-Path $NodeDir) { Remove-Item $NodeDir -Recurse -Force }
    New-Item -ItemType Directory -Path $NodeDir | Out-Null

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($NodeZipPath)
    foreach ($entry in $zip.Entries) {
        $entryPath = $entry.FullName -replace "^[^/]+/", ""
        if (-not $entryPath) { continue }
        $destPath = Join-Path $NodeDir $entryPath
        $destDir  = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        if (-not $entry.FullName.EndsWith("/")) {
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $destPath, $true)
        }
    }
    $zip.Dispose()
    Remove-Item $NodeZipPath -Force -ErrorAction SilentlyContinue

    Write-Host "  [OK] Node.js extraido correctamente." -ForegroundColor Green
    $UseGlobal = $false
}

# ── Configurar PATH para esta sesion ────────────────────────────────
if (-not $UseGlobal) {
    $env:PATH = "$NodeDir;$env:PATH"
}

Set-Location $ProjectDir

# ── Función helper para ejecutar comandos sin errores por warnings ───
function Run-Cmd {
    param([string]$cmd)
    cmd /c "$cmd 2>&1"
    return $LASTEXITCODE
}

# ── Paso 3: Instalar dependencias ───────────────────────────────────
Write-Host ""
Write-Host "  [3/4] Instalando dependencias..." -ForegroundColor Yellow
Write-Host "        (Primera vez puede tardar 3-5 min)" -ForegroundColor Gray
Write-Host ""

if ($UseGlobal) {
    cmd /c "npm install --prefer-offline 2>&1"
} else {
    cmd /c "`"$NodeExe`" `"$NpmScript`" install --prefer-offline 2>&1"
}

if ($LASTEXITCODE -ne 0) {
    # Intentar de nuevo sin offline
    Write-Host "  Reintentando..." -ForegroundColor Yellow
    if ($UseGlobal) {
        cmd /c "npm install 2>&1"
    } else {
        cmd /c "`"$NodeExe`" `"$NpmScript`" install 2>&1"
    }
}

# Verificar que node_modules existe
if (-not (Test-Path (Join-Path $ProjectDir "node_modules"))) {
    Write-Host ""
    Write-Host "  [ERROR] No se instalaron las dependencias correctamente." -ForegroundColor Red
    Read-Host "`n  Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "  [OK] Dependencias instaladas." -ForegroundColor Green

# ── Paso 4: Compilar el .exe ────────────────────────────────────────
Write-Host ""
Write-Host "  [4/4] Compilando el .exe..." -ForegroundColor Yellow
Write-Host "        (Descargando Electron ~100MB y empaquetando)" -ForegroundColor Gray
Write-Host "        Por favor espera, puede tomar 5-10 minutos..." -ForegroundColor Gray
Write-Host ""

if ($UseGlobal) {
    cmd /c "npm run build 2>&1"
} else {
    cmd /c "`"$NodeExe`" `"$NpmScript`" run build 2>&1"
}

$buildCode = $LASTEXITCODE

# ── Resultado ───────────────────────────────────────────────────────
$DistDir  = Join-Path $ProjectDir "dist"
$exeFiles = @()
if (Test-Path $DistDir) {
    $exeFiles = Get-ChildItem $DistDir -Filter "*.exe" -ErrorAction SilentlyContinue
}

if ($exeFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Green
    Write-Host "   EXE CREADO EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "  ============================================================" -ForegroundColor Green
    Write-Host ""
    foreach ($exe in $exeFiles) {
        $sizeMB = [math]::Round($exe.Length / 1MB, 0)
        Write-Host "    $($exe.Name)  ($sizeMB MB)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "    Ubicacion: $DistDir" -ForegroundColor Gray
    Write-Host ""
    Start-Process "explorer.exe" $DistDir
} else {
    Write-Host ""
    Write-Host "  [ERROR] No se encontro el .exe en dist/" -ForegroundColor Red
    Write-Host "  Codigo de salida del build: $buildCode" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Revisa los mensajes de error arriba." -ForegroundColor Yellow
}

Read-Host "`n  Presiona Enter para salir"
