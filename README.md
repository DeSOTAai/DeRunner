# Instalation

* If model allready instaled function as upgrade since the the installer crawl newest installer from github - Take a look into Installer Optional `Arguments`
* Install python if not exist
* Download miniconda, git and nssm as portables to Desota Folder
* Clone GitHub Repository
* Copy config_template into User main config.yaml
* Create a virtual environment with miniconda
* Start Server after instalation - Take a look into Installer Optional `Arguments`

<details>
    <summary><h2>Windows</h2></summary>

* Go to CMD as Administrator (command prompt):
    * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
    * Search: `cmd` 
    * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

* Copy-Paste the following comands: 
    ```cmd
    powershell -command "Invoke-WebRequest -Uri https://github.com/desotaai/derunner/raw/main/Executables/Windows/DeRunner.install.bat -OutFile ~\derunner_installer.bat" && call %UserProfile%\derunner_installer.bat && del %UserProfile%\derunner_installer.bat

    ```
    * Installer Optional `Arguments`

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

# Service Operations

* Start/Stop Service

<details>
    <summary><h2>Windows</h2></summary>

* Go to CMD (command prompt):
  * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
  * Search: `cmd` 
  * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

### Start Service
* Copy-Paste the following comands: 
    ```cmd
    %UserProfile%\Desota\DeRunner\executables\Windows\derruner.start.bat

    ```
### Stop Service
* Copy-Paste the following comands: 
    ```cmd
    %UserProfile%\Desota\DeRunner\executables\Windows\derruner.stop.bat

    ```
</details>

# Uninstalation

* Delete Service
* Delete DeRunner Folder

<details>
    <summary><h2>Windows</h2></summary>

* Go to CMD (command prompt):
  * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
  * Search: `cmd` 
  * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

* Copy-Paste the following comands: 
    ```cmd
    %UserProfile%\Desota\DeRunner\executables\Windows\derruner.uninstall.bat

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

