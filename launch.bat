@echo off
setlocal
set PYTHONPATH=
set PYTHONHOME=
set VIRTUAL_ENV=

set "PYTHON=C:\Users\user\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"

cd /d "C:\Users\user\corp-recon-engine"
"%PYTHON%" -B launch_app.py

endlocal
