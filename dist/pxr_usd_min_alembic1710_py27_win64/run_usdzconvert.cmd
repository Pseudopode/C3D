@echo off
setlocal
pushd %~dp0

set DEPS=%~dp0\USD\deps
set USD_BIN=%~dp0\USD\bin
set USD_LIB=%~dp0\USD\lib
set USD_LIB_PYTHON=%~dp0\USD\lib\python

set PYTHON27_DEPS=%DEPS%\python
set USDVIEW_PYTHON27_DEPS=%DEPS%\usdview-deps-python
set USD_PLUGIN=%~dp0\USD\plugin\usd
set USDZCONVERT_LIB=%~dp0\usduconvert

echo Adding to PYTHONPATH
echo "%USD_LIB_PYTHON%"
echo "%USDVIEW_PYTHON27_DEPS%"
echo "%USDZCONVERT_LIB%"
set PYTHONPATH=%USD_LIB_PYTHON%;%USDVIEW_PYTHON27_DEPS%;%USDZCONVERT_LIB%;

echo Adding to PATH
echo "%PYTHON27_DEPS%"
echo "%USD_BIN%"
echo "%USD_LIB%"
echo "%USD_PLUGIN%"
set PATH=%PYTHON27_DEPS%;%USD_LIB%;%USD_BIN%;%USD_PLUGIN%;

set INTERPRETER=%~dp0\USD\deps\python\python.exe

"%INTERPRETER%" "%~dp0\usdzconvert\usdzconvert" %*
