@echo off
title Compilando .exe - Traductor de Juegos
echo.
echo  Iniciando compilador...
echo  (Se abrira una ventana de PowerShell con el progreso)
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0compilar.ps1"
