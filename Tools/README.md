# builtin_model_tester example cmds

## WINDOWS
### DeUrlCruncher
```
%UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/deurlcruncher --expert web-scraper --input-type text --input-file "Search Engine" --report-file %UserProfile%\Desota\duc_report.json
```
### DeScraper/Url:
```
%UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/descraper/url --expert web-scraper --input-dict "{'url':['https://pt.wikipedia.org/wiki/Os_Simpsons']}" --report-file %UserProfile%\Desota\descraper_url_report.json
```
### DeScraper/Html:
```
%UserProfile%\Desota\DeRunner\env\python.exe %UserProfile%\Desota\DeRunner\Tools\builtin_model_tester.py --model franciscomvargas/descraper/html --expert web-scraper --input-dict "{'url':['https://pt.wikipedia.org/wiki/Os_Simpsons']}" --report-file %UserProfile%\Desota\descraper_html_report.json
```



## LINUX
### DeUrlCruncher
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/deurlcruncher --expert web-scraper --input-type text --input-file "Search Engine" --report-file ~/Desota/duc_report.json
```
### Whisper:
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/whisper.cpp --expert audio-recognition --input-type audio
--input-file 'Desota/Desota_Models/WhisperCpp/samples/jfk.wav' --report-file ~/Desota/whisper_report.json
```
### DeScraper/Url:
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/descraper/url --expert web-scraper --input-dict '{"url":"https://pt.wikipedia.org/wiki/Os_Simpsons"}' --report-file Desota\descraper_report.json
```
### DeScraper/Html:
```
~/Desota/DeRunner/env/bin/python3 ~/Desota/DeRunner/Tools/builtin_model_tester.py --model franciscomvargas/descraper/html --expert web-scraper --input-dict '{"url":"https://pt.wikipedia.org/wiki/Os_Simpsons"}' --report-file ~/Desota/descraper_report.json
```