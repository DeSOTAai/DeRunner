@REM  VARS 
for %%a in ("%~dp0..\..") do set "model_path_run=%%~fa"
@REM Go to Project Folder
call cd %model_path_run%
@REM Run DeRunner
call %model_path_run%\env\python DeRunner.py
PAUSE