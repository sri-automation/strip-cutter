@echo off
rem Opens the Strip Cutter Control panel in its own window (Microsoft Edge, app mode).
rem The panel is the file StripCutterControl.html in this same folder.
set "PAGE=%~dp0StripCutterControl.html"
if not exist "%PAGE%" (
  echo StripCutterControl.html is not in this folder.
  pause
  exit /b 1
)
start "" msedge --app="file:///%PAGE:\=/%" --window-size=1240,940
if errorlevel 1 start "" "%PAGE%"
