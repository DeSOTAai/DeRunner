![DeSOTA Welcome](Assets/Logo_DeSota.png)

<details open>
   <summary><h1>DeRunner Overview</h1></summary>

[![Models Requests](Assets/DeManagertools_ModelsRequests.png)](https://github.com/DeSOTAai/DeManagerTools#models--tools-dashboard)

Derunner consists on a python scrip running as service to:
 - Serve as main client for DeSOTA API Models Request, for example `DeSOTA Tools` (eg. [DeUrlCruncher](https://github.com/franciscomvargas/DeUrlCruncher)) and `DeSOTA AI Models` (eg. [DeScraper](https://github.com/franciscomvargas/descraper), [NeuralQA](https://github.com/franciscomvargas/neuralqa));
 - Automatically Upgrade `DeSOTA Tools` and `DeSOTA AI Models`;
 - Automatically Re-Install `DeSOTA Tools` and `DeSOTA AI Models` on critical errors.

</details>




<details open>
    <summary><h1>Instalation</h1></summary>

## Use DeSOTA official [Manager & Tools](https://github.com/DeSOTAai/DeManagerTools#readme)

1. [Download Installer for your Platform](https://github.com/DeSOTAai/DeManagerTools#dedicated-installer)
  
2. **Open** [`Models Instalation`](https://github.com/DeSOTAai/DeManagerTools/#install--upgrade-desota-models-and-tools) tab

3. **Select** the Available Tool `desotaai/derunner`

4. **Press** `Start Instalation`

<details>
    <summary><h2>Manual Windows Instalation</h2></summary>

* Go to CMD (command prompt):
  * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
  * Enter: `cmd` 
  * <kbd>↵ Enter</kbd>

### Download:

1. Create Model Folder:
```cmd
rmdir /S /Q %UserProfile%\Desota\DeRunner
mkdir %UserProfile%\Desota\DeRunner

```

2. Download Last Release:
```cmd
powershell -command "Invoke-WebRequest -Uri https://github.com/desotaai/derunner/archive/refs/tags/v0.0.0.zip -OutFile %UserProfile%\DeRunner_release.zip" 

```

3. Uncompress Release:
```cmd
tar -xzvf %UserProfile%\DeRunner_release.zip -C %UserProfile%\Desota\DeRunner --strip-components 1 

```

4. Delete Compressed Release:
```cmd
del %UserProfile%\DeRunner_release.zip

```

### Setup:

5. Setup:
```cmd
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.setup.bat

```

*  Optional Arguments:
    <table>
        <thead>
            <tr>
                <th>arg</th>
                <th>Description</th>
                <th>Example</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>/debug</td>
                <td>Log everything (useful for debug)</td>
                <td><code>%UserProfile%\Desota\DeRunner\executables\Windows\derunner.setup.bat /debug</code></td>
            </tr>
            <tr>
                <td>/manualstart</td>
                <td>Don't start at end of setup</td>
                <td><code>%UserProfile%\Desota\DeRunner\executables\Windows\derunner.setup.bat /manualstart</code></td>
            </tr>
        </tbody>
    </table>
    
</details>



<details>
    <summary><h2>Manual Linux Instalation</h2></summary>

* Go to Terminal:
    * <kbd> Ctrl </kbd> + <kbd> Alt </kbd> + <kbd>T</kbd>

### Download:

1. Create Model Folder:
```cmd
rm -rf ~/Desota/DeRunner
mkdir -p ~/Desota/DeRunner

```

2. Download Last Release:
```cmd
wget https://github.com/franciscomvargas/descraper/archive/refs/tags/v0.0.0.zip -O ~/DeRunner_release.zip

```

3. Uncompress Release:
```cmd
sudo apt install libarchive-tools -y && bsdtar -xzvf ~/DeRunner_release.zip -C ~/Desota/DeRunner --strip-components=1

```

4. Delete Compressed Release:
```cmd
rm -rf ~/DeRunner_release.zip

```

### Setup:

5. Setup:
```cmd
sudo bash ~/Desota/DeRunner/executables/Linux/derunner.setup.bash

```

*  Optional Arguments:
    <table>
        <thead>
            <tr>
                <th>arg</th>
                <th>Description</th>
                <th>Example</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>-d</td>
                <td>Setup with debug Echo ON</td>
                <td><code>sudo bash ~/Desota/DeRunner/executables/Linux/derunner.setup.bash -d</code></td>
            </tr>
            <tr>
                <td>-m</td>
                <td>Don't start service at end of setup</td>
                <td><code>sudo bash ~/Desota/DeRunner/executables/Linux/derunner.setup.bash -m</code></td>
            </tr>
        </tbody>
    </table>
    
    
</details>
</details>




<details open>
    <summary><h1>Service Operations</h1></summary>

<details>
    <summary><h2>Windows</h2></summary>

* Go to CMD as Administrator (command prompt):
  * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
  * Enter: `cmd` 
  * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

### Start Service
```cmd
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.start.bat

```

### Stop Service
```cmd
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.stop.bat

```

### Status Service
```cmd
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.status.bat

```

</details>



<details>
    <summary><h2>Linux</h2></summary>

* Go to Terminal:
    * <kbd> Ctrl </kbd> + <kbd> Alt </kbd> + <kbd>T</kbd>

### Start Service
```cmd
sudo bash ~/Desota/DeRunner/executables/Linux/derunner.start.bash

```
    
### Stop Service
```cmd
sudo bash ~/Desota/DeRunner/executables/Linux/derunner.stop.bash

```

### Status Service
```cmd
bash ~/Desota/DeRunner/executables/Linux/derunner.status.bash

```

</details>
</details>




<details open>
    <summary><h1>Uninstalation</h1></summary>

## Use DeSOTA official [Manager & Tools](https://github.com/DeSOTAai/DeManagerTools#readme)

1. **Open** [`Models Dashboard`](https://github.com/DeSOTAai/DeManagerTools/#models--tools-dashboard) tab

2. **Select** the model `franciscomvargas/descraper`

3. **Press** `Uninstall`

<details>
    <summary><h2>Manual Windows Uninstalation</h2></summary>

* Go to CMD as Administrator (command prompt):
  * <kbd>⊞ Win</kbd> + <kbd>R</kbd>
  * Enter: `cmd` 
  * <kbd>Ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>↵ Enter</kbd>

```cmd
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.uninstall.bat

```

* Optional `Arguments`

    |arg|Description|Example
    |---|---|---|
    |/Q|Uninstall without requiring user interaction|`%UserProfile%\Desota\DeRunner\executables\Windows\derunner.uninstall.bat /Q`
      
</details>



<details>
    <summary><h2>Manual Linux Uninstalation</h2></summary>

* Go to Terminal:
    * <kbd> Ctrl </kbd> + <kbd> Alt </kbd> + <kbd>T</kbd>

```cmd
sudo bash ~/Desota/DeRunner/executables/Linux/derunner.uninstall.bash

```

* Optional `Arguments`

    |arg|Description|Example
    |---|---|---|
    |-q|Uninstall without requiring user interaction|`sudo bash ~/Desota/DeRunner/executables/Linux/derunner.uninstall.bash -q`
      
</details>
</details>




<details open>
    <summary><h1>Credits / Lincense</h1></summary>

## [DeSOTA](https://desota.net/)
```sh
@credit{
  ai2023desota,
  title = "DeRunner: Main Runner for Desota Servers",
  authors = ["Kristian Atanasov", "Francisco Vargas"],
  url = "https://desota.net/",
  year = 2023
}
```
</details>

