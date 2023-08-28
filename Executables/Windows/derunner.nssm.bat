@ECHO OFF
:: - Model Path
set model_path=%UserProfile%\Desota\DeRunner
:: Service VARS
:: retrieved from https://nssm.cc/usage
set model_name=DeRunner
set service_name=derunner_service
set exe_path=%model_path%\executables\Windows
set model_exe=%exe_path%\derunner.service.bat
set model_exe_args=
set model_desc=
set model_dependencies=
set model_log=%model_path%\service.log
set model_env=



:: -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

:: NSSM - the Non-Sucking Service Manager 
IF EXIST %UserProfile%\Desota\Portables\nssm goto endofnssm 
call mkdir %UserProfile%\Desota\Portables\nssm >NUL 2>NUL
call cd %UserProfile%\Desota\Portables\nssm >NUL 2>NUL
call powershell -command "Invoke-WebRequest -Uri https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip -OutFile ~\Desota\Portables\nssm.zip" &&  tar -xzvf %UserProfile%\Desota\Portables\nssm.zip -C %UserProfile%\Desota\Portables\nssm --strip-components 1 && del %UserProfile%\Desota\Portables\nssm.zip
:endofnssm

:: NSSM - exe path 
IF %PROCESSOR_ARCHITECTURE%==AMD64 set nssm_exe=%UserProfile%\Desota\Portables\nssm\win64\nssm.exe
IF %PROCESSOR_ARCHITECTURE%==x86 set nssm_exe=%UserProfile%\Desota\Portables\nssm\win32\nssm.exe

:: Service Install
call %nssm_exe% install %service_name% %model_exe% %exe_path% >NUL 2>NUL
:: Application tab
:: call %nssm_exe% set %service_name% Application %model_exe%
call %nssm_exe% set %service_name% AppDirectory %exe_path% >NUL 2>NUL
call %nssm_exe% set %service_name% AppParameters server >NUL 2>NUL
:: Details tab
call %nssm_exe% set %service_name% DisplayName Desota/%model_name% >NUL 2>NUL
call %nssm_exe% set %service_name% Description %model_desc% >NUL 2>NUL
call %nssm_exe% set %service_name% Start SERVICE_AUTO_START >NUL 2>NUL
:: Log on tab
call %nssm_exe% set %service_name% ObjectName LocalSystem >NUL 2>NUL
call %nssm_exe% set %service_name% Type SERVICE_WIN32_OWN_PROCESS >NUL 2>NUL
:: Dependencies
call %nssm_exe% set %service_name% DependOnService %model_dependencies% >NUL 2>NUL

:: Process tab
call %nssm_exe% set %service_name% AppPriority NORMAL_PRIORITY_CLASS >NUL 2>NUL
call %nssm_exe% set %service_name% AppNoConsole 0 >NUL 2>NUL
call %nssm_exe% set %service_name% AppAffinity All >NUL 2>NUL
:: Shutdown tab
call %nssm_exe% set %service_name% AppStopMethodSkip 0 >NUL 2>NUL
call %nssm_exe% set %service_name% AppStopMethodConsole 1500 >NUL 2>NUL
call %nssm_exe% set %service_name% AppStopMethodWindow 1500 >NUL 2>NUL
call %nssm_exe% set %service_name% AppStopMethodThreads 1500 >NUL 2>NUL
:: Exit actions tab
call %nssm_exe% set %service_name% AppThrottle 1500 >NUL 2>NUL
call %nssm_exe% set %service_name% AppExit Default Restart >NUL 2>NUL
call %nssm_exe% set %service_name% AppRestartDelay 0 >NUL 2>NUL
:: I/O tab
call %nssm_exe% set %service_name% AppStdout %model_log% >NUL 2>NUL
call %nssm_exe% set %service_name% AppStderr %model_log% >NUL 2>NUL
:: File rotation tab
call %nssm_exe% set %service_name% AppStdoutCreationDisposition 4 >NUL 2>NUL
call %nssm_exe% set %service_name% AppStderrCreationDisposition 4 >NUL 2>NUL
call %nssm_exe% set %service_name% AppRotateFiles 1 >NUL 2>NUL
call %nssm_exe% set %service_name% AppRotateOnline 0 >NUL 2>NUL
call %nssm_exe% set %service_name% AppRotateSeconds 86400 >NUL 2>NUL
call %nssm_exe% set %service_name% AppRotateBytes 1048576 >NUL 2>NUL
:: Environment tab
call %nssm_exe% set %service_name% AppEnvironmentExtra %model_env% >NUL 2>NUL

exit