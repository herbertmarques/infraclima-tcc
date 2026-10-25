@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado. Instale Python 3.10 ou superior e tente novamente.
  pause
  exit /b 1
)
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo O InfraClima requer Python 3.10 ou superior.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  if errorlevel 1 goto :error
) else (
  call .venv\Scripts\activate.bat
)
start "InfraClima" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8000"
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
goto :eof
:error
echo Falha ao preparar o ambiente. Verifique a conexao com a internet e as instrucoes do README.
pause
exit /b 1
