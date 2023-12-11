@ECHO OFF
:: Get Model path
:: %~dp0 = C:\users\[user]\Desota\DeRunner\executables\Windows
for %%a in ("%~dp0..\..") do set "model_path=%%~fa"
:: Move to Model Path
call cd %model_path%
:: Delete Service Log on-start
break>%model_path%\service.log
:: Make sure every package required is installed
call %model_path%\env\python -m pip install -r %model_path%\requirements.txt
:mainloop
:: Start DeRunner Service
call %model_path%\env\python DeRunner.py
IF errorlevel 66 GOTO exit_mainloop
GOTO mainloop

:exit_mainloop
ECHO DeRunner Requested EXIT
start /B /WAIT %model_path%\executables\windows\derunner.stop.bat
exit