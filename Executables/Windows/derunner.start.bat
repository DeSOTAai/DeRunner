@ECHO OFF
:: Service VARS
set service_name=derunner_service
:: Service waiter - Confirm Service is ready for requests
set model_path_str=%UserProfile%\Desota\DeRunner
set service_waiter=%model_path_str%\env\python %model_path_str%\DeRunner.py --handshake
set shake_respose={"status":"ready"}



:: -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

:: NSSM - exe path 
IF %PROCESSOR_ARCHITECTURE%==AMD64 set nssm_exe=%UserProfile%\Desota\Portables\nssm\win64\nssm.exe
IF %PROCESSOR_ARCHITECTURE%==x86 set nssm_exe=%UserProfile%\Desota\Portables\nssm\win32\nssm.exe

:: Start service - retrieved from https://nssm.cc/commands
call %nssm_exe% start %service_name% >NUL

:: Wait for Service to be fully started
:waitloop
%service_waiter% > %UserProfile%\tmpFile.txt
set /p service_res= < %UserProfile%\tmpFile.txt
del %UserProfile%\tmpFile.txt > NUL 2>NUL
IF '%service_res%' NEQ '%shake_respose%' (
    timeout 2 > NUL 2>NUL
    GOTO waitloop
)

:: EOF
call %nssm_exe% status %service_name%
exit