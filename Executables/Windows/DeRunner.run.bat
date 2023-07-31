@REM Go to Project Folder
call cd %UserProfile%\Desota\DeRunner
@REM Activate Conda Virtual Environment
call %UserProfile%\miniconda3\condabin\conda activate ./env
@REM Run ZapCrawler
call python DeRunner.py
PAUSE