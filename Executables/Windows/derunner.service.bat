@ECHO OFF
:mainloop

@REM Get Model path
for %%a in ("%~dp0..\..") do set "model_path_serv=%%~fa"

@REM Run DeRunner
call cd %model_path_serv%
call %model_path_serv%\env\python DeRunner.py >NUL 2>NUL

GOTO mainloop