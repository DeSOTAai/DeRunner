@ECHO OFF
:mainloop

:: Get Model path
:: %~dp0 = C:\users\[user]\Desota\DeRunner\executables\Windows
for %%a in ("%~dp0..\..") do set "model_path_serv=%%~fa"

:: Run DeRunner Service
call cd %model_path_serv%
call %model_path_serv%\env\python DeRunner.py

IF errorlevel 66 GOTO exit_mainloop

GOTO mainloop

:exit_mainloop
ECHO DeRunner Requested EXIT
start /B /WAIT %model_path_serv%\executables\windows\derunner.stop.bat
exit