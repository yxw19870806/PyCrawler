@echo off
cd /D %~dp0\win32

echo update pip
C:\Python27\python.exe -m pip install --upgrade pip

echo install pyWin32
C:\python27\Scripts\pip.exe install pywin32-220.1-cp27-cp27m-win32.whl
::C:\python27\Scripts\pip.exe install http://www.lfd.uci.edu/~gohlke/pythonlibs/f9r7rmd8/pywin32-220.1-cp27-cp27m-win32.whl
C:\Python27\python.exe C:\python27\Scripts\pywin32_postinstall.py -install

echo install pyHook
C:\python27\Scripts\pip.exe install pyHook-1.5.1-cp27-cp27m-win32.whl
::C:\python27\Scripts\pip.exe install http://www.lfd.uci.edu/~gohlke/pythonlibs/f9r7rmd8/pyHook-1.5.1-cp27-cp27m-win32.whl

pause