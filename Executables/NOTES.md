# WINDOWS

## Project comands

### SETUP CMD:
```
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.setup.bat /startmodel
```


### START CMD:
```
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.start.bat
```


### STOP CMD:
```
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.stop.bat
```


### STATUS CMD:
```
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.status.bat
```


### Uninstall CMD:
```
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.uninstall.bat /Q
```


### INSTALL SERVICE CMD:
```
%UserProfile%\Desota\DeRunner\executables\Windows\derunner.nssm.bat
```



## Service commands

### Start Service:
```
%UserProfile%\Desota\Portables\nssm\win64\nssm.exe start derunner_service
```


### Stop Service

```
%UserProfile%\Desota\Portables\nssm\win64\nssm.exe stop derunner_service
```


### Status Service:
```
%UserProfile%\Desota\Portables\nssm\win64\nssm.exe status derunner_service
```


### Remove Service:
```
%UserProfile%\Desota\Portables\nssm\win64\nssm.exe remove derunner_service
```





# LINUX

## Project executables

### REQUIRED APT INSTALLS
apt install openssl

### SETUP:
```
sudo /bin/bash ~/Desota/DeRunner/executables/Linux/derunner.setup.bash -s
```


### UNINSTALL:
```
sudo /bin/bash ~/Desota/DeRunner/executables/Linux/derunner.uninstall.bash
```
