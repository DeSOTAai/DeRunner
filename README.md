# Instalation
<details>
    <summary><h2>Windows</h2></summary>

### Create Project Folder 
**Model PATH:** `%UserProfile%\Desota_Models\DeRunner`

* Open CMD:
    * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
    * Search: `cmd` <br>

* Copy-Paste the following comands: 
```cmd
mkdir %UserProfile%\Desota\DeRunner
cd %UserProfile%\Desota\DeRunner

```

### Test if conda is instaled

Copy-Paste the following comands 
```cmd
%UserProfile%\miniconda3\condabin\conda --version
```
if response is:
>  '`YourUserPath`\miniconda3\condabin\conda' is not recognized as an internal or external command, operable program or batch file.

then is required conda instalation !

### Conda Instalation
Copy-Paste the following comand
```sh
powershell -command "Invoke-WebRequest -Uri https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -OutFile ~\miniconda.exe && start /B /WAIT %UserProfile%\miniconda.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\miniconda3 && del %UserProfile%\miniconda.exe 

```

### Install DeRunner
Copy-Paste the following comands 
```cmd
cd %UserProfile%\Desota\DeRunner
git clone https://github.com/desotaai/derunner.git .
%UserProfile%\miniconda3\condabin\conda create --prefix ./env python=3.11 -y
%UserProfile%\miniconda3\condabin\conda activate ./env
pip install -r requirements.txt
copy %UserProfile%\Desota\DeRunner\Assets\config_template.yaml %UserProfile%\Desota\DeRunner\config.yaml
echo INSTALATION DONE 
echo [ WARNING ]  - Is Required to configure Desota API Key in %UserProfile%\Desota\DeRunner\config.yaml

```
</details>

# Run
<details>
    <summary><h2>Windows</h2></summary>

* Open CMD:
    * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
    * Search: `cmd` <br>

* Copy-Paste the following comands: 
```cmd
cd %UserProfile%\Desota\DeRunner
%UserProfile%\miniconda3\condabin\conda activate ./env
python DeRunner.py

```
</details>

# Credits / Lincense

## [DeSOTA](#coming-soon)
```sh
@credit{
  ai2023desota,
  title = "DeRunner: Main Runner for Desota Servers",
  authors = ["Kristian Atanasov", "Francisco Vargas"],
  url = "https://github.com/desotaai/derunner/",  #eventually the desota webpage
  year = 2023
}
```
</details>

