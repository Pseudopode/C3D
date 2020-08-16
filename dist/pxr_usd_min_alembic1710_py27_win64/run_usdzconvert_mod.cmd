@echo off
setlocal
pushd %~dp0

set "v=%~dp0"
set "v2=%v:\=/%"
echo.%v2%

set DEPS=%v2%/USD/deps
set USD_BIN=%v2%/USD/bin
set USD_LIB=%v2%/USD/lib
set USD_LIB_PYTHON=%v2%/USD/lib/python

set PYTHON27_DEPS=%DEPS%/python
set USDVIEW_PYTHON27_DEPS=%DEPS%/usdview-deps-python
set USD_PLUGIN=%v2%/USD/plugin/usd
set USDZCONVERT_LIB=%v2%/usduconvert

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

set INTERPRETER=%v2%/USD/deps/python/python.exe

%INTERPRETER% "%v2%/usdzconvert/usdzconvert" %*
