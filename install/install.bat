@echo off
echo update pip
C:\Python27\python.exe -m pip install --upgrade pip

echo install pillow
C:\python27\Scripts\pip.exe install Pillow

echo install pyHook
C:\python27\Scripts\pip.exe install pyHook

echo install pyWin32
C:\python27\Scripts\pip.exe install pywin32
C:\Python27\python.exe C:\python27\Scripts\pywin32_postinstall.py -install

echo install pyquery
C:\python27\Scripts\pip.exe install pyquery

echo install urllib3
C:\python27\Scripts\pip.exe install urllib3

echo install PyCrypto
C:\python27\Scripts\pip.exe install PyCrypto

pause
