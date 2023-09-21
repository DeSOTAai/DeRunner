<details open>
    <summary><h1>Instalation</h1></summary>

* If model allready installed this installer function as upgrade, since the the installer webrequest newest installer from github - Take a look into [Installer Optional Arguments](#installer-optional-arguments)
* Install python if not exist
* Download miniconda, git and nssm as portables to Desota Folder
* Clone GitHub Repository
* Create a virtual environment with miniconda
* Start Server after instalation - Take a look into [Installer Optional Arguments](#installer-optional-arguments)

<details open>
    <summary><h2>Use DeSOTA official <a href="https://github.com/DeSOTAai/DeManagerTools/">Manager Tools</a></h2></summary>

[![Install DeManagerTools](https://img.shields.io/static/v1?label=Desota%20-%20Manager%20Tools&message=Install&color=blue&logo=windows)](https://minhaskamal.github.io/DownGit/#/home?url=https://github.com/DeSOTAai/DeManagerTools/blob/main/executables/Windows/demanagertools.install.bat)

<!-- TODO: Convert desota host into HTTPS -->
<!-- [![Install DeManagerTools](https://img.shields.io/static/v1?label=Desota%20-%20Manager%20Tools&message=Install&color=blue&logo=windows)](http://129.152.27.36/assistant/download.php?system=win&file=demanagertools) -->

1. Uncompress File
2. Run .BAT file
</details>

<details open>
    <summary><h2>Manual Windows Instalation</h2></summary>

* Go to CMD as Administrator (command prompt):
    * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
    * Search: `cmd` 
    * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

* Copy-Paste the following comands: 
    ```cmd
    powershell -command "Invoke-WebRequest -Uri https://github.com/desotaai/derunner/raw/main/Executables/Windows/DeRunner.install.bat -OutFile ~\derunner_installer.bat" && call %UserProfile%\derunner_installer.bat && del %UserProfile%\derunner_installer.bat

    ```
### Installer Optional Arguments

<table>
    <thead>
        <tr>
            <th>arg</th>
            <th>Description</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan=3>/reinstall</td>
            <td>Overwrite project when re-installing</td>
        </tr>
        <tr>
            <td>Delete project service when re-installing</td>
        </tr>
        <tr>
            <td>Install without requiring user interaction</td>
        </tr>
        <tr>
            <td>/startmodel</td>
            <td>Start project service after instalation</td>
        </tr>
    </tbody>
</table>

`Install with overwrite permission and start server after instalation`

```cmd
powershell -command "Invoke-WebRequest -Uri https://github.com/desotaai/derunner/raw/main/Executables/Windows/DeRunner.install.bat -OutFile ~\derunner_installer.bat" && call %UserProfile%\derunner_installer.bat /reinstall /startmodel && del %UserProfile%\derunner_installer.bat

```
    
    
</details>
</details>

<details open>
    <summary><h1>Service Operations</h1></summary>

<details open>
    <summary><h2>Windows</h2></summary>

* Go to CMD (command prompt):
  * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
  * Search: `cmd` 
  * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

### Start Service
* Copy-Paste the following comands: 
    ```cmd
    %UserProfile%\Desota\DeRunner\executables\Windows\derunner.start.bat

    ```
### Stop Service
* Copy-Paste the following comands: 
    ```cmd
    %UserProfile%\Desota\DeRunner\executables\Windows\derunner.stop.bat

    ```
</details>
</details>

<details open>
    <summary><h1>Uninstalation</h1></summary>

* Delete Service
* Delete DeRunner Folder

## Use DeSOTA official [Manager Tools](https://github.com/DeSOTAai/DeManagerTools/)

<details open>
    <summary><h2>Manual Windows Uninstalation</h2></summary>

* Go to CMD (command prompt):
  * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
  * Search: `cmd` 
  * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

* Copy-Paste the following comands: 
    ```cmd
    %UserProfile%\Desota\DeRunner\executables\Windows\derunner.uninstall.bat

    ```
    * Uninstaller Optional `Arguments`

        |arg|Description|
        |---|---|
        |/Q|Uninstall without requiring user interaction|
        
        `Uninstall Quietly`
        
        ```cmd
        %UserProfile%\Desota\Desota_Models\NeuralQA\neuralqa\executables\Windows\neuralqa.uninstall.bat /Q

        ```
      
</details>
</details>

<details open>
    <summary><h1>Credits / Lincense</h1></summary>

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

