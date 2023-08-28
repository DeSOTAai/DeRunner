@ECHO OFF
:: Uninstalation VARS
:: - Model Path
set model_path=%UserProfile%\Desota\DeRunner
set service_name=derunner_service
set nssm_path=%UserProfile%\Desota\Portables\nssm



:: -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

:: IPUT ARGS - /Q=Quietly
SET arg1=/Q

:: NSSM - exe VAR 
IF %PROCESSOR_ARCHITECTURE%==AMD64 set nssm_exe=%nssm_path%\win64\nssm.exe
IF %PROCESSOR_ARCHITECTURE%==x86 set nssm_exe=%nssm_path%\win32\nssm.exe

IF "%1" EQU "" GOTO noargs
IF %1 EQU /Q (
    :: Delete Model Service - retrieved from https://nssm.cc/commands
    call %nssm_exe% remove %service_name% confirm
    :: Delete Project Folder
    IF EXIST %model_path% rmdir /S /Q %model_path%
    GOTO EOF_UN
)

:noargs
:: Delete Model Service - retrieved from https://nssm.cc/commands
call %nssm_exe% stop %service_name%
call %nssm_exe% remove %service_name%
:: Delete Project Folder
IF EXIST %model_path% (
    rmdir /S %model_path%
    GOTO EOF_UN
)

:EOF_UN
:: Inform Uninstall Completed
call %nssm_exe% status %service_name%
IF NOT EXIST %model_path% echo DeRunner Uninstalled!
