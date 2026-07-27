@echo off
title Traductor de Juegos en Tiempo Real
echo  Iniciando Traductor de Juegos...
call npm start
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] La aplicacion no pudo iniciarse.
    echo  Asegurate de haber ejecutado instalar.bat primero.
    pause
)
