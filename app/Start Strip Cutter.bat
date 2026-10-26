@echo off
rem Opens the Strip Cutter v5 app in its own window (Microsoft Edge, app mode).
rem The app is the file StripCutter.html in this same folder. USB needs DIP switches 3 and 4 ON.
set "PAGE=%~dp0StripCutter.html"
if not exist "%PAGE%" (
  echo StripCutter.html is not in this folder.
  pause
  exit /b 1
)
start "" msedge --app="file:///%PAGE:\=/%" --window-size=1240,940
if errorlevel 1 start "" "%PAGE%"
