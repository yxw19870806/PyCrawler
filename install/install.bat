@echo off
echo update pip
C:\Python27\python.exe -m pip install --upgrade pip

echo install Pillow
C:\python27\Scripts\pip.exe install Pillow

echo install PyHook
C:\python27\Scripts\pip.exe install pyHook

echo install PyWin32
C:\python27\Scripts\pip.exe install pywin32
C:\Python27\python.exe C:\python27\Scripts\pywin32_postinstall.py -install

echo install PyCrypto
C:\python27\Scripts\pip.exe install PyCrypto

echo install Urllib3
C:\python27\Scripts\pip.exe install urllib3

echo install PyQuery
C:\python27\Scripts\pip.exe install pyquery

pause
