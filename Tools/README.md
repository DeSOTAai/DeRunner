<!-- Overview -->
# Built-In Model Tester

*Simulate Model Request with same logic as in `DeRunner.py`*

### The `builtin_model_tester.py` script tasks:

* **Developers**: Test in-development stage models before publish it to DeSOTA.

* **DeSOTA OS**: Test Model Setup after istalation & unhandled errors.

<br><br>

<!-- Section: Developers Usage -->
# Developers Usage

## ◦ Model [DeUrlCruncher](https://github.com/franciscomvargas/deurlcruncher)

![Windows Terminal](https://img.shields.io/badge/Windows%20Terminal-%234D4D4D.svg?style=for-the-badge&logo=windows-terminal&logoColor=white)
```
%UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/deurlcruncher --expert web-scraper --input-type text --input-file "Search Engine" --report-file %UserProfile%\Desota\duc_report.json
```
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/deurlcruncher --expert web-scraper --input-type text --input-file "Search Engine" --report-file ~/Desota/duc_report.json
```

## ◦ Model [DeScraper](https://github.com/franciscomvargas/descraper)

![Windows Terminal](https://img.shields.io/badge/Windows%20Terminal-%234D4D4D.svg?style=for-the-badge&logo=windows-terminal&logoColor=white)
* **Parent-Model: descraper/url**
    ```
    %UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/descraper/url --expert web-scraper --input-dict "{'url':['https://pt.wikipedia.org/wiki/Os_Simpsons']}" --report-file %UserProfile%\Desota\descraper_url_report.json
    ```
* **Child-Model: descraper/html**
    ```
    %UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/descraper/html --expert web-scraper --input-dict "{'url':['https://pt.wikipedia.org/wiki/Os_Simpsons']}" --report-file %UserProfile%\Desota\descraper_html_report.json
    ```

![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
* **Parent-Model: descraper/url**
    ```
    sudo ~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/descraper/url --expert web-scraper --input-dict '{"url":"https://pt.wikipedia.org/wiki/Os_Simpsons"}' --report-file Desota\descraper_url_report.json
    ```
* **Child-Model: descraper/html**
    ```
    sudo ~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/descraper/html --expert web-scraper --input-dict '{"url":"https://pt.wikipedia.org/wiki/Os_Simpsons"}' --report-file ~/Desota/descraper_html_report.json
    ```

## ◦ Model [WhisperCpp](https://github.com/franciscomvargas/whisper.cpp)

![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/whisper.cpp --expert audio-recognition --input-type audio
--input-file 'Desota/Desota_Models/WhisperCpp/samples/jfk.wav' --report-file ~/Desota/whispercpp_report.json
```

<br><br>


<!-- Section: DeSOTA OS Usage -->
# DeSOTA OS Usage

## ◦ Model [DeUrlCruncher](https://github.com/franciscomvargas/deurlcruncher)

![Windows Terminal](https://img.shields.io/badge/Windows%20Terminal-%234D4D4D.svg?style=for-the-badge&logo=windows-terminal&logoColor=white)
```
%UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/deurlcruncher
```
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/deurlcruncher
```

## ◦ Model [DeScraper](https://github.com/franciscomvargas/descraper)

![Windows Terminal](https://img.shields.io/badge/Windows%20Terminal-%234D4D4D.svg?style=for-the-badge&logo=windows-terminal&logoColor=white)
```
%UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/descraper/url
```
```
%UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/descraper/html
```
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
```
sudo ~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/descraper/url
```
```
sudo ~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/descraper/html
```

## ◦ Model [WhisperCpp](https://github.com/franciscomvargas/whisper.cpp)

![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/whisper.cpp
```