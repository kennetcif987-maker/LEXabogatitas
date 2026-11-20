@echo off
title LeX IA 360 - Suite Juridica Forense
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================================
echo        INICIANDO LEX IA 360 (SAAS LEGAL)
echo ==========================================================
echo.
echo Verificando puertos e iniciando Lex IA 360...
echo.
python -m streamlit run app.py
