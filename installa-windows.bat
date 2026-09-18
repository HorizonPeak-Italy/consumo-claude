@echo off
setlocal EnableExtensions
title Consumo Claude - installazione
echo.
echo   Consumo Claude  -  Horizon Peak srls  -  horizonpeak.it
echo   =======================================================
echo.

set "ORIGINE=%~dp0"
set "DEST=%LOCALAPPDATA%\consumo-claude"

rem Aperto da dentro lo ZIP senza estrarlo: manca il resto del programma.
if not exist "%ORIGINE%consumo_claude\__main__.py" (
  echo   Prima estrai lo ZIP: tasto destro sul file ZIP, "Estrai tutto",
  echo   poi apri questo file dalla cartella estratta.
  echo   First extract the ZIP ^(right click, "Extract all"^), then run this file again.
  echo.
  pause
  exit /b 1
)

rem ---- 1. Python 3.8 o successivo ----
call :trova_python
if not defined PY (
  echo   Python 3 non e' installato.  /  Python 3 is not installed.
  where winget >nul 2>&1
  if errorlevel 1 goto python_a_mano
  choice /c SN /m "  Lo installo adesso? / Install it now? (S=si/yes, N=no)"
  if errorlevel 2 goto python_a_mano
  winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
  call :trova_python
)
if not defined PY goto python_a_mano
echo   Python: %PY%

rem ---- 2. Copia in una cartella stabile ----
echo   Copio il programma in %DEST%
robocopy "%ORIGINE%." "%DEST%" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo   Copia non riuscita.  /  Copy failed.
  pause
  exit /b 1
)

rem ---- 3. Avvio con doppio clic e icona sul desktop ----
> "%DEST%\Consumo Claude.bat" (
  echo @echo off
  echo cd /d "%%~dp0"
  echo %PY% -m consumo_claude %%*
  echo echo.
  echo pause
)
> "%DEST%\Disinstalla.bat" (
  echo @echo off
  echo echo Disinstallo Consumo Claude...
  echo where claude ^>nul 2^>^&1 ^&^& call claude plugin uninstall consumo-claude@horizonpeak ^>nul 2^>^&1
  echo where claude ^>nul 2^>^&1 ^&^& call claude plugin marketplace remove horizonpeak ^>nul 2^>^&1
  echo powershell -NoProfile -Command "Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Consumo Claude.lnk') -ErrorAction SilentlyContinue"
  echo echo Fatto. / Done.
  echo pause
  echo cd /d "%%TEMP%%"
  echo rmdir /s /q "%DEST%"
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Desktop'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'Consumo Claude.lnk')); $s.TargetPath=$env:DEST + '\Consumo Claude.bat'; $s.WorkingDirectory=$env:DEST; $s.Description='Consumo Claude - Horizon Peak srls'; $s.Save()"
if errorlevel 1 (
  echo   Icona sul desktop non creata: il programma si avvia da "%DEST%\Consumo Claude.bat"
) else (
  echo   Icona "Consumo Claude" creata sul desktop.
)

rem ---- 4. Comando /consumo dentro Claude Code ----
where claude >nul 2>&1
if errorlevel 1 (
  echo   Claude Code non trovato: /consumo si aggiunge rilanciando questo file dopo averlo installato.
  goto fine
)
call claude plugin marketplace add "%DEST%" >nul 2>&1 || call claude plugin marketplace update horizonpeak >nul 2>&1
call claude plugin uninstall consumo-claude@horizonpeak >nul 2>&1
call claude plugin install consumo-claude@horizonpeak
if errorlevel 1 (
  echo   /consumo non aggiunto a Claude Code. L'icona sul desktop funziona comunque.
) else (
  echo   Comando /consumo aggiunto a Claude Code.
)

:fine
echo.
echo   Installazione completata.  /  Installation complete.
echo   Per disinstallare: "%DEST%\Disinstalla.bat"
echo.
choice /c SN /m "  Vuoi vedere subito il consumo? / Show usage now? (S/N)"
if errorlevel 2 exit /b 0
call "%DEST%\Consumo Claude.bat"
exit /b 0

:python_a_mano
echo.
echo   Installa Python dalla pagina che si apre ^(spunta "Add python.exe to PATH"^),
echo   poi riapri questo file.
echo   Install Python from the page that opens ^(tick "Add python.exe to PATH"^),
echo   then run this file again.
start "" "https://www.python.org/downloads/windows/"
pause
exit /b 1

:trova_python
set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>&1 && set "PY=py -3" && exit /b 0
python -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>&1 && set "PY=python" && exit /b 0
rem Appena installato da winget il PATH di questa finestra non e' ancora aggiornato.
for %%P in ("%LOCALAPPDATA%\Programs\Python\Launcher\py.exe") do if exist %%P set "PY="%%~P" -3" && exit /b 0
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set "PY="%%D\python.exe""
exit /b 0
