@ECHO OFF
:mainloop

:: Get Model path
for %%a in ("%~dp0..\..") do set "model_path_serv=%%~fa"

:: Run DeRunner Service
call cd %model_path_serv%
call %model_path_serv%\env\python DeRunner.py

GOTO mainloop