@REM Instalation VARS
@REM Model GIT
set model_git=https://github.com/desotaai/derunner.git
set model_git_branch=main
@REM - Model Path
set model_path=%UserProfile%\Desota\DeRunner
@REM - Service Name
set model_service_name=derunner_service
@REM - Model Execs
set model_uninstall=%model_path%\executables\Windows\derunner.uninstall.bat
set model_service_install=%model_path%\executables\Windows\derunner.nssm.bat
set model_start=%model_path%\executables\Windows\derunner.start.bat



@REM -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

@REM - Program Installers
set python64=https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe
set python32=https://www.python.org/ftp/python/3.11.4/python-3.11.4.exe
set git64_portable=https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/PortableGit-2.41.0.3-64-bit.7z.exe
set git32_portable=https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/PortableGit-2.41.0.3-32-bit.7z.exe
set miniconda64=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
set miniconda32=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86.exe

@REM IPUT ARGS - /reinstall="overwrite model + remove service" ; /startmodel="Start Model Service"
SET arg1=/reinstall
SET arg2=/startrunner

@REM Re-instalation Check
IF NOT EXIST %model_path% GOTO endofreinstall
IF "%1" EQU "" GOTO noreinstallargs
IF %1 EQU %arg1% (
    GOTO reinstall
)
IF %2 EQU %arg1% (
    GOTO reinstall
)
:noreinstallargs
call %model_uninstall%
GOTO endofreinstall
:reinstall
call %model_uninstall% /Q
:endofreinstall
IF EXIST %model_path% echo Re-Instalation Required && GOTO EOF_IN

@REM Create Project Folder
mkdir %model_path%
call cd %model_path%


@REM Install Python if Required
python --version 3>NUL
IF errorlevel 1 (
    python3 --version 3>NUL
    IF errorlevel 1 (
        IF NOT EXIST %UserProfile%\Desota\Portables\python3 (
            GOTO installpython
        )
    )
)
goto skipinstallpython
:installpython
call mkdir %UserProfile%\Desota\Portables
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %python64% -OutFile ~\python3_installer.exe" && start /B /WAIT %UserProfile%\python3_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 TargetDir=%UserProfile%\Desota\Portables\python3 && del %UserProfile%\python3_installer.exe && goto skipinstallpython
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %python32% -OutFile ~\python3_installer.exe" && start /B /WAIT %UserProfile%\python3_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 TargetDir=%UserProfile%\Desota\Portables\python3 && del %UserProfile%\python3_installer.exe && goto skipinstallpython
:skipinstallpython

@REM GIT MODEL CLONE
git --version 3>NUL
IF NOT errorlevel 1 (
    @REM  Clone Descraper Repository
    call git clone --branch %model_git_branch% %model_git% .
    call copy %model_path%\Assets\config_template.yam %model_path%\config.yaml
    GOTO endgitclonemodel
)
@REM PORTABLE GIT MODEL CLONE
@REM Install Portable Git
call mkdir %UserProfile%\Desota\Portables
IF EXIST %UserProfile%\Desota\Portables\PortableGit GOTO clonerep
@REM Install Portable Git
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %git64_portable% -OutFile ~\Desota\Portables\git_installer.exe" && start /B /WAIT %UserProfile%\Desota\Portables\git_installer.exe -o"%UserProfile%\Desota\Portables\PortableGit" -y && del %UserProfile%\Desota\Portables\git_installer.exe && goto clonerep
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %git32_portable% -OutFile ~\Desota\Portables\git_installer.exe" && start /B /WAIT %UserProfile%\Desota\Portables\git_installer.exe -o"%UserProfile%\Desota\Portables\PortableGit" && del %UserProfile%\Desota\Portables\git_installer.exe && goto clonerep
:clonerep
call %UserProfile%\Desota\Portables\PortableGit\bin\git.exe clone --branch %model_git_branch% %model_git% .
:endgitclonemodel


@REM Install Conda if Required
call mkdir %UserProfile%\Desota\Portables
IF NOT EXIST %UserProfile%\Desota\Portables\miniconda3\condabin\conda.bat goto installminiconda
goto skipinstallminiconda
:installminiconda
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %miniconda64% -OutFile %UserProfile%\miniconda_installer.exe" && start /B /WAIT %UserProfile%\miniconda_installer.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\Desota\Portables\miniconda3 && del %UserProfile%\miniconda_installer.exe && goto skipinstallminiconda
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %miniconda32% -OutFile %UserProfile%\miniconda_installer.exe" && start /B /WAIT %UserProfile%\miniconda_installer.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\Desota\Portables\miniconda3 && del %UserProfile%\miniconda_installer.exe && && goto skipinstallminiconda
:skipinstallminiconda


@REM Create/Activate Conda Virtual Environment
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda create --prefix ./env python=3.11 -y
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda activate ./env

@REM Install required Libraries
call pip install -r requirements.txt


@REM Install Service - NSSM  - the Non-Sucking Service Manager
start /B /WAIT %model_service_install%



@REM Start Runner Service?
IF "%1" EQU "" GOTO EOF_IN
IF %1 EQU %arg2% (
    GOTO startrunner
)
IF "%2" EQU "" GOTO EOF_IN
IF %2 EQU %arg2% (
    GOTO startrunner
)
@REM :nostartargs
@REM SET /P STARTRUNNER=Instalation Completed! Start Runner? (Y/[N])?
@REM IF /I "%STARTRUNNER%" NEQ "Y" GOTO startrunner
@REM IF /I "%STARTRUNNER%" NEQ "y" GOTO startrunner
@REM IF /I "%STARTRUNNER%" NEQ "yes" GOTO startrunner
GOTO EOF_IN

:startmodel
start /B /WAIT %model_start%
call echo Model [ %model_service_name% ] - Started!

:EOF_IN
call echo Instalation Completed!!
call timeout 30
exit