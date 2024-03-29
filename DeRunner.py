import sys, os, io, time
import json, ast, re
import shutil, traceback

import subprocess, requests
from subprocess import check_output
from subprocess import check_call, call, CalledProcessError
from subprocess import Popen
try: 
    from subprocess import CREATE_NEW_CONSOLE
except:
    pass
    
# import pyyaml module
import yaml
from yaml.loader import SafeLoader

from desota import detools
I=0
DEBUG = False
DEVELOPMENT = False
if len(sys.argv)>1:
    if "-dev" in sys.argv:
        DEVELOPMENT = True
    if "-deb" in sys.argv:
        DEBUG = True
    if "-cli" in sys.argv:
        CLI_MODE = True
        
USER_SYS = detools.get_platform()
    
# :: os.getcwd() = C:\users\[user]\Desota\DeRunner
# WORKING_FOLDER = os.getcwd()
APP_PATH = os.path.dirname(os.path.realpath(__file__))
if USER_SYS == "win":
    path_split = str(APP_PATH).split("\\")
    USER=path_split[-3]
    USER_PATH = "\\".join(path_split[:-2])
elif USER_SYS == "lin":
    path_split = str(APP_PATH).split("/")
    USER=path_split[-3]
    USER_PATH = "/".join(path_split[:-2])
STATUS_PATH = os.path.join(APP_PATH, "status.txt")
    
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
LOG_PATH = os.path.join(DESOTA_ROOT_PATH, "demanager.log")
TMP_PATH=os.path.join(DESOTA_ROOT_PATH, "tmp")
if not os.path.isdir(TMP_PATH):
    os.mkdir(TMP_PATH)
    detools.user_chown(TMP_PATH)

CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
if not os.path.isdir(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)
    detools.user_chown(CONFIG_PATH)
USER_CONF_PATH = os.path.join(CONFIG_PATH, "user.config.yaml")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")
LAST_SERV_CONF_PATH = os.path.join(CONFIG_PATH, "latest_services.config.yaml")
LAST_UP_EPOCH = os.path.join(CONFIG_PATH, "last_upgrade_epoch.txt")

#!!!! Upgrade Frequency in secs
UPG_FREQ = 86400    # 24h
# UPG_FREQ = 10     # DEBUG

# Services Configurations
#   - DeRunner service name
DERRUNER_ID = "desotaai/derunner"
#   - Latest version URL
LATEST_SERV_CONF_RAW = "https://raw.githubusercontent.com/DeSOTAai/DeRunner/main/Assets/latest_services.config.yaml"

API_URL = "https://desota.net/assistant/api.php"
API_UP =  "https://desota.net/assistant/api_uploads"

DEFAULT_MODEL_TIMEOUT = 3600
# models=['audio-classification-efficientat', 'whisper-small-en', 'coqui-tts-male', 'lllyasviel/sd-controlnet-seg-text-to-image','lllyasviel/sd-controlnet-openpose-text-to-image','lllyasviel/sd-controlnet-normal-text-to-image','lllyasviel/sd-controlnet-mlsd-text-to-image','lllyasviel/sd-controlnet-hed-text-to-image','lllyasviel/sd-controlnet-depth-text-to-image','lllyasviel/sd-controlnet-canny-text-to-image','lllyasviel/sd-controlnet-openpose-control','lllyasviel/sd-controlnet-normal-control','lllyasviel/sd-controlnet-mlsd-control','lllyasviel/sd-controlnet-hed-control','lllyasviel/sd-controlnet-canny-control','lllyasviel/sd-controlnet-text','clip','basic-vid2vid','basic-txt2vid','watch-video','talking-heads','clip-2','clip-2']


# Utils Funcs
def remove_single_quotes(text):
    pattern = r"\['(.*?)'\]"
    matches = re.findall(pattern, text)
    for match in matches:
        replaced_match = match.replace("'", "")
        text = text.replace(f"['{match}']", f"['{replaced_match}']")
    return text
def json_comquotes(raw_json, lone_char_searches=2, debug=False):
    try:
        out_json = json.loads(raw_json)
        return out_json
    except:
        try:
            out_json = ast.literal_eval(raw_json)
            return out_json
        except:
            # prepare raw json from some unwanted scenarios 
            raw_json = raw_json.replace(": '", ":'").replace(", '", ",'").replace("{ '", "{'").replace("[ '", "['").replace("' }", "'}").replace("' }", "'}").replace("''", "' '")
            raw_json = raw_json.replace(': "', ':"').replace(', "', ',"').replace('{ "', '{"').replace('[ "', '["').replace('" }', '"}').replace('" }', '"}').replace('""', '" "')

            # Regex patterns : dq|sq stands for double|single quote(s)
            _re_dq_pattern = r'([\s\w])"([\s\w])'
            _re_dq_sub = r"\1\"\2"
            _re_sq_pattern = r"([\s\w])'([\s\w])"
            _re_sq_sub = r'\1\'\2'
            
            for _lone_char in range(lone_char_searches):
                # Substitute Double Quotes
                if _lone_char == 0:
                    _re_find = re.sub(_re_dq_pattern, _re_dq_sub, raw_json)
                #   > Solve schenarios like ""a"a"a"a"a" since 1st return "a\"a"a\"a"a", second time return a\"a\"a\"a\"a" (Other egs. ["Anything"a"Anything else", "Anything"a"Anythin"g" else"])
                else:
                    _re_find = re.sub(_re_dq_pattern, _re_dq_sub, _re_find)

                # Substitute Single Quote   > Solve schenarios like 'a'a'a' since 1st return 'a\'a'a', secund time return 'a\'a\'\a' ...
                _re_find = re.sub(_re_sq_pattern, _re_sq_sub, _re_find)

                if debug:
                    print(f"Iteration #{_lone_char+1}:", _re_find)

                try:
                    out_json = json.loads(_re_find)
                    # Rem space from raw_json.replace("''", "' '").replace('""', '" "')
                    _re_find= _re_find.replace('\\" "', '\\""').replace('\\" \\"', '\\"\\"').replace("\\' '", "\\''").replace("\\' \\'", "\\'\\'")
                    return json.loads(_re_find)
                except Exception as ej:
                    try:
                        out_json = ast.literal_eval(_re_find)
                        # Rem space from raw_json.replace("''", "' '").replace('""', '" "')
                        _re_find= _re_find.replace('\\" "', '\\""').replace("\\' '", "\\''")
                        return ast.literal_eval(_re_find)
                    except Exception as ea:
                        if _lone_char != lone_char_searches-1:
                            continue
                        raise ValueError(f"Json Parse exception: {ej}\nAst Parse exception : {ea}\nProcessed Json      : {_re_find}")
#   > Find JSON OBJ in STR
def find_json(s):
    s = s.replace("\'", "\"")
    start = s.find("{")
    end = s.rfind("}")
    res = s[start:end+1]
    res = res.replace("\n", "")
    return res
#   > Conditional print
def cprint(query, condition=DEBUG):
    '''Conditional print'''
    if condition:
        print(query)
#   > Log to demanager.log
def delogger(query):
    if not os.path.isfile(LOG_PATH):
        with open(LOG_PATH, "w") as fw:
            fw.write(f"File Forced Creation by DeRunner\n")

    with open(LOG_PATH, "a") as fa:
        if isinstance(query, str) or isinstance(query, int) or isinstance(query, float):
            fa.write(f"{query}\n")
        elif isinstance(query, list):
            fa.writelines(query)
        elif isinstance(query, dict):
            fa.write(json.dumps(query, indent=2))
            fa.write("\n")
    detools.user_chown(LOG_PATH)
# Decifer Desota Files
def fix_file_name(file_name):
    # TEMPORARY FIX
    # retrieved from https://stackoverflow.com/a/3642850 & https://stackoverflow.com/a/32680048
    _file_pattern = re.compile(r'file\(((.)*)\)')
    _file_res = _file_pattern.search(file_name)
    if _file_res:
        file_name = _file_res.group(1)
    _text_pattern = re.compile(r'text\(((.)*)\)')
    _text_res = _text_pattern.search(file_name)
    if _text_res:
        file_name = _text_res.group(1)
    _audio_pattern = re.compile(r'audio\(((.)*)\)')
    _audio_res = _text_pattern.search(file_name)
    if _audio_res:
        file_name = _audio_res.group(1)
    return file_name
# Simple Post Request
def simple_post(url, data, timeout=None):
    _http_connect = True
    while True:
        try:
            response = requests.post(url, data=data, timeout=timeout)
            if not _http_connect:
                print(f"[ INFO ] -> DeRunner Internet Acess Re-Established")
                delogger(f"[ INFO ] -> DeRunner Internet Acess Re-Established")
            return response
        except requests.exceptions.ConnectionError as cerr:
            if _http_connect:
                print(f"[ WARNING ] -> DeRunner Lost Internet Acess: {cerr}")
                delogger(f"[ WARNING ] -> DeRunner Lost Internet Acess: {cerr}")
            _http_connect = False
            pass
        except requests.exceptions.ConnectTimeout as cto:
            if _http_connect:
                print(f"[ WARNING ] -> DeRunner Lost Internet Acess: {cto}")
                delogger(f"[ WARNING ] -> DeRunner Lost Internet Acess: {cto}")
            _http_connect = False
            pass
        except requests.exceptions.ReadTimeout as rto:
            if _http_connect:
                print(f"[ WARNING ] -> DeRunner Lost Internet Acess: {rto}")
                delogger(f"[ WARNING ] -> DeRunner Lost Internet Acess: {rto}")
            _http_connect = False
            pass
    return response
def check_status():
    if USER_SYS != "lin":
        return
    _status = None
    if not os.path.isfile(STATUS_PATH):
        print("STATUS FILE NOT FOUND!")
        with open(STATUS_PATH, "w") as fw:
            fw.write("0")
            _status =  0
    with open(STATUS_PATH, "r") as fr:
        _status  = int(fr.read().strip())
    if _status == 1:
        print("[ INFO ] -> DeRunner Service Stop Requested!")
        print("Start CMD:\tsudo systemctl start derunner.service")
        delogger([
            "[ INFO ] -> DeRunner Service Stop Requested!\n",
            "  Start CMD: sudo systemctl start derunner.service\n"
        ])
        exit(66)


# DeRunner Class
class Derunner():
    # Configurations
    def __init__(self, ignore_update=DEVELOPMENT) -> None:
        self.serv_conf, self.last_serv_conf = self.get_services_config(ignore_update=ignore_update)
        self.user_conf = self.get_user_config()
        self.user_models = self.user_conf['models']
        self.user_api_key = self.user_conf['api_key']
        if USER_SYS == "win":
            self.pypath = os.path.join(APP_PATH, "env", "python.exe")
        elif USER_SYS == "lin":
            self.pypath = os.path.join(APP_PATH, "env", "bin", "python3")

    #   > Grab User Configurations
    def get_user_config(self) -> dict:
        if not os.path.isfile(USER_CONF_PATH):
            _template_user_conf={
                "api_key": None,
                "models":None,
                "system": USER_SYS
            }
            with open(USER_CONF_PATH, 'w',) as fw:
                yaml.dump(_template_user_conf,fw,sort_keys=False)
            detools.user_chown(USER_CONF_PATH)
            return _template_user_conf
        with open( USER_CONF_PATH ) as f_user:
            return yaml.load(f_user, Loader=SafeLoader)
    
    def add_quarantine_model(self, model_ids):
        if isinstance(model_ids, str):
            model_ids = [model_ids]
        quarantine_config_key = "quarantine"
        # Assert quarantine config_key
        user_config = self.get_user_config()
        try:
            assert user_config[quarantine_config_key]
        except:
            user_config[quarantine_config_key] = {}
        for model in model_ids:
            model_version = None
            # Get Model Version
            try:
                assert user_config["models"][model]
                model_version = user_config["models"][model]
            except:
                pass
            try:
                serv_config, latest_serv_config = self.get_services_config(ignore_update=False)
                try:
                    assert serv_config["services_params"][model]
                    service_config = serv_config["services_params"][model]
                    parent_model = model
                    if service_config["submodel"]:
                        parent_model = service_config["parent_model"]
                    if not model_version:
                        assert serv_config["services_params"][parent_model]
                        model_version = serv_config["services_params"][parent_model][USER_SYS]["version"]
                except:
                    try:
                        assert latest_serv_config["services_params"][model]
                        service_config = latest_serv_config["services_params"][model]
                        parent_model = model
                        if service_config["submodel"]:
                            parent_model = service_config["parent_model"]
                        if not model_version:
                            assert serv_config["services_params"][parent_model]
                            model_version = serv_config["services_params"][parent_model][USER_SYS]["version"]
                    except:
                        continue
            except:
                continue
            try:
                assert parent_model
                assert model_version
            except:
                continue
            print(f"[ INFO ] -> New quarantine model:\n\tID: {parent_model}\n\t#V: {model_version}")
            delogger([
                f"[ INFO ] -> New quarantine model:\n",
                f"         ID: {parent_model}:\n", 
                f"    Version: {model_version}:\n",
            ])
            if model not in user_config[quarantine_config_key] and model_version:
                user_config[quarantine_config_key][parent_model] = model_version

        self.set_user_config(user_config)

    def set_user_config(self, configs):
        with open( USER_CONF_PATH, "w" ) as f_user:
            yaml.dump(configs,f_user,sort_keys=False)
    
    #   > Return latest_services.config.yaml(write if not ignore_update)
    def get_services_config(self, ignore_update=False) -> (dict, dict):
        _req_res = None
        check_status()
        if not ignore_update:
            try:
                _req_res = requests.get(LATEST_SERV_CONF_RAW)
            except requests.exceptions.ConnectionError as cerr:
                cprint(f"[ WARNING ] -> DeRunner Lost Internet Acess: {cerr}", DEBUG)
                ignore_update = True
                pass
            except requests.exceptions.ConnectTimeout as cto:
                cprint(f"[ WARNING ] -> DeRunner Lost Internet Acess: {cto}", DEBUG)
                ignore_update = True
                pass
            except requests.exceptions.ReadTimeout as rto:
                cprint(f"[ WARNING ] -> DeRunner Lost Internet Acess: {rto}", DEBUG)
                ignore_update = True
                pass
        check_status()
        if ignore_update or ( isinstance(_req_res, requests.Response) and _req_res.status_code != 200 ):
            if not (os.path.isfile(SERV_CONF_PATH) or os.path.isfile(LAST_SERV_CONF_PATH)):
                print(f" [SERV_CONF] Not found-> {SERV_CONF_PATH}")
                print(f" [LAST_SERV_CONF] Not found-> {LAST_SERV_CONF_PATH}")
                raise EnvironmentError()
            else:
                with open( SERV_CONF_PATH ) as f_curr:
                    with open(LAST_SERV_CONF_PATH) as f_last:
                        return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)
        check_status()
        if _req_res.status_code == 200:
            # Create Latest Services Config File
            with open(LAST_SERV_CONF_PATH, "w") as fw:
                fw.write(_req_res.text)
            detools.user_chown(LAST_SERV_CONF_PATH)

        check_status()
        # Create Services Config File if don't exist
        if not os.path.isfile(SERV_CONF_PATH):
            with open(LAST_SERV_CONF_PATH) as fls:
                _template_serv=yaml.load(fls, Loader=SafeLoader)
             
            _user_models = self.get_user_config()["models"]
            _user_serv_params = {}
            if _user_models:
                for _model in _user_models:
                    _params = _template_serv["services_params"][_model]
                    _user_serv_params[_model] = _params
                    if "child_models" in _params and _params["child_models"]:
                        for _child in  _params["child_models"]:
                            if _child in _template_serv["services_params"]:
                                _user_serv_params[_child] = _template_serv["services_params"][_child]

            _template_serv["services_params"] = _user_serv_params
            with open(SERV_CONF_PATH, "w") as fw:
                yaml.dump(_template_serv,fw,sort_keys=False)
            detools.user_chown(SERV_CONF_PATH)

        check_status()
        with open( SERV_CONF_PATH ) as f_curr:
            with open(LAST_SERV_CONF_PATH) as f_last:
                return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)

    def set_services_config(self, configs):
        with open( SERV_CONF_PATH, "w" ) as f_serv:
            yaml.dump(configs,f_serv,sort_keys=False)

    # DeSOTA API Monitor
    def grab_runner_models(self, update=True) -> list:
        if update:
            user_conf = self.get_user_config()
        else:
            user_conf = self.user_conf
        try:
            user_models = user_conf["models"]
        except:
            return []
        runner_models = []
        if not user_models:
            return runner_models
        for model in user_models:
            try:
                try:
                    model_params = self.serv_conf["services_params"][model]
                except:
                    model_params = self.last_serv_conf["services_params"][model]
                if model_params["service_type"] != "asset":
                    runner_models.append(model)
            except:
                continue
        return runner_models
    
    #   > Check for model request
    def monitor_model_request(self, user_models, debug=False) -> dict:
        global I
        I += 1
        cprint(f"Running...{I}", debug) 
        selected_task = False
        model_request_dict = {
            "task_type": None,      # TASK VARS
            "task_model": None,
            "task_dep": None,
            "task_args": None,
            "task_id": None,
        }
        '''
        Additional model_request_dict keys:
        {
            "input_args":{          # INPUT VARS
                "file": [
                    {
                        "file_name": ,
                        "file_url":
                    },
                    ...
                ],
                "image": [
                    {
                        "file_name": ,
                        "file_url":
                    },
                    ...
                ]
                "audio": [
                    {
                        "file_name": ,
                        "file_url":
                    },
                    ...
                ]
                "video": [
                    {
                        "file_name": ,
                        "file_url":
                    },
                    ...
                ]
                "text_prompt": ["What is the content of this file?", ...]
                **aditional iputs .. test and see
            },       
            "dep_args":{            # DEPENDENCIES VARS
                [dep_id_0]:{
                    "file": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ],
                    "image": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ]
                    "audio": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ]
                    "video": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ]
                    "text_prompt": ["What is the content of this file?", ...]
                    **aditional iputs .. test and see
                },       
                }
                [dep_id_1]:{
                    "file": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ],
                    "image": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ]
                    "audio": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ]
                    "video": [
                        {
                            "file_name": ,
                            "file_url":
                        },
                        ...
                    ]
                    "text_prompt": ["What is the content of this file?", ...]
                    **aditional iputs .. test and see
                }
                (...)
            }
        }
        '''
        # User Models
        cprint(f"[ INFO ] -> All User Models: {json.dumps(user_models, indent=4)}", debug)

        if not user_models:
            return None
        
        for model in user_models:
            '''
            Send a POST request to API to get a task
                Return: `task`
            ''' 

            data = {
                "api_key":self.user_api_key,
                "model":model
            }
            
            task = simple_post(API_URL, data=data, timeout=5)

            cprint(f"\nSignal DeSOTA that Model is wake up:\n{json.dumps(data, indent=2)}", debug)
            cprint(f"Response Status = {task.status_code}", debug)
            if task.status_code != 200:
                continue

            '''
            Send a POST request to select a task
                Return: `select_task`
            ''' 
            data = {
                "api_key":self.user_api_key,
                "model":user_models,
                "select_task":I
            }
            
            select_task = simple_post(API_URL, data=data, timeout=5)

            cprint(f"Task Selection Request Payload:\n{json.dumps(data, indent=2)}", debug)
            cprint(f"Response Status = {task.status_code}", debug)
            cprint(f"\n\n\n[ DEBUG ] -> MODEL REQ. Response Body: {select_task.text}\n\n\n", debug)
            if select_task.status_code != 200:
                continue
            I=I+1
            
            
            
            cont = str(select_task.content.decode('UTF-8'))
            print(cont)
            try:
                # print(selected_task)
                selected_task = json.loads(str(cont.decode('UTF-8')))
                cont=remove_single_quotes(cont)
                cprint(f"MODEL: {select_task['model']}", debug)
                selected_model = select_task['model']
                # print(json.dumps(selected_task, indent=2))
            except:
                cont = cont.replace("FIXME!!!", "")
                #cont = cont.replace('\\', '')
                cont = cont.replace('\\\\', '')
                cprint(f"[ INFO ] -> API MODEL REQUEST FORMAT NOT JSON!\nResponse: {cont}", debug)   
                ''' 
                cont = cont.replace("\n", "")
                #cont = cont.replace(r'\\\\', "")
                #cont = cont.replace("\\\\\\", "")
                #cont = cont.replace('\\', '')
                #cont = cont.replace("\n", "")
                #cont = cont.replace("\\", "")
                '''
                
                try:
                    selected_task = json_comquotes(cont, debug=True)
                except:
                    cont = cont.replace('\\', '')
                    try:
                        selected_task = json_comquotes(cont)
                    except:
                        selected_task = "error"
                    # print(selected_task)

            if "error" in selected_task:
                #error = selected_task['error']
                cprint(f"[ WARNING ] -> API Model Request fail", debug)
                selected_task = False
                continue
            
            # cprint(selected_task, debug)     
            #cprint(selected_task['task'], debug)
            
            print("[ DEBUG ] DeSOTA API Request", json.dumps(selected_task, indent=2))
            try:
                task_dic = ast.literal_eval(str(selected_task['task']))
            except:
                task_dic = None

            if isinstance(task_dic, dict) and task_dic:
                model_request_dict['input_args'] = {}

                ######
                ###### DeScraper Gets file in URL! TODO: Improve
                ######
                try:
                    assert task_dic["url"]
                    _tmp_target = [i for i in task_dic["url"]]
                    for _iter_url in task_dic["url"]:
                        if len(detools.get_url_from_str(_iter_url)) == 0:
                            try:
                                assert task_dic["file"]
                            except:
                                task_dic["file"] = []
                            
                            task_dic["file"].append(_iter_url)
                            task_dic["url"].remove(_iter_url)

                    if not task_dic["url"]:
                        del task_dic["url"]
                except:
                    pass

                for file_type, file_values in task_dic.items():
                    if isinstance(file_values, str):
                        file_values = [file_values]
                    if not isinstance(file_values, list):
                        continue
                    for duck_file in file_values:
                        file_value_fixed = fix_file_name(duck_file)
                        #print(file_type)

                        if file_type == "text":
                            # cprint(f'text select on 0', debug)
                            try:
                                assert model_request_dict['input_args']['text_prompt']
                            except:
                                model_request_dict['input_args']['text_prompt'] = []
                            model_request_dict['input_args']['text_prompt'].append(detools.download_file(file_value_fixed, get_file_content=True))
                        elif file_type in ['image', 'video', 'audio', 'file']:
                            try:
                                assert model_request_dict['input_args'][file_type]
                            except:
                                model_request_dict['input_args'][file_type] = []
                            model_request_dict['input_args'][file_type].append({
                                "file_name": str(file_value_fixed),
                                "file_url": f"{API_UP}/{file_value_fixed}"
                            })
                        else:
                            try:
                                assert model_request_dict['input_args'][file_type]
                            except:
                                model_request_dict['input_args'][file_type] = []
                            model_request_dict['input_args'][file_type].append(detools.download_file(file_value_fixed))
                            
                cprint(f"Request INPUT Files: {json.dumps(model_request_dict['input_args'], indent=2)}", debug)
                    
                model_request_dict["task_type"] = selected_task['type']
                model_request_dict["task_model"] = selected_task['model']
                task_dep = str(selected_task['dep']).replace("\\\\n", "").replace("\\", "")
                task_dep = ast.literal_eval(task_dep)
                model_request_dict["task_dep"] = task_dep
                cprint(f"task type is {model_request_dict['task_type']}", debug)     
                # cprint(f"task deps are {task_dep} {type(task_dep[0])}", debug)   
                cprint(f"task deps are {task_dep}", debug)   
                #if json.loads(str(task_dep.decode('UTF-8'))):
                
                print(f"\n\n\n[ DEBUG ] model_request_dict: {model_request_dict}\n\n\n")
                print(f"\n\n\n[ DEBUG ] selected_task: {selected_task}\n\n\n")
                
                ## Model Request Mutations ~ Handle New User Prompt 
                if model_request_dict['input_args']['text_prompt']:
                    try:
                        assert selected_task["arg"]["prompt"]
                        if selected_task["arg"]["prompt"] != "$initial-prompt$":
                            model_request_dict['input_args']['text_prompt'] = [selected_task["arg"]["prompt"]]
                        del selected_task["arg"]["prompt"]
                    except Exception:
                        pass
                
                ## Append Model Request Arguments(dict) from DeSOTA API
                try:
                    assert selected_task["arg"]
                    if selected_task["arg"]:
                        model_request_dict['input_args']['model_args'] = selected_task["arg"]
                except Exception:
                        pass
                


                # TODO: Implement Dependencies Args!!

                # if task_dep != [-1]:
                #     cprint("Dependencies:", debug)   
                #     #deps = json.loads(str(task_dep.decode('UTF-8')))
                #     model_request_dict['dep_args'] = {}
                #     for dep_key, dep_args in task_dep.items():
                #         if isinstance(dep_args, str):
                #             dep_args = [dep_args]
                #         if not isinstance(dep_args, list):
                #             continue
                #         for duck_file in dep_args:
                #             print("[ DEBUG ] duck_file(" + str(type(duck_file)) + ")", duck_file)
                #             file_value_fixed = fix_file_name(duck_file)
                #             try:
                #                 dep_id = int(dep_key)
                #                 dep_dic = json.loads(str(dep_args))
                #             except:
                #                 try:
                #                     dep_dic = find_json(str(dep_args))
                #                     dep_dic = json.loads(dep_dic)   
                #                 except:
                #                     dep_dic = None
                #                     if not model_request_dict['dep_args'] and debug:
                #                         cprint("no filename found" , debug)
                #             if dep_dic:
                #                 model_request_dict['dep_args'][dep_id] = {}
                #                 for file_type, file_value in dep_dic.items():
                #                     file_value_fixed = fix_file_name(file_value)
                #                     #print(file_type)
                #                     if file_type == "text":
                #                         # cprint(f'text select on 0', debug)
                #                         try:
                #                             assert model_request_dict['dep_args'][dep_id]['text_prompt']
                #                         except:
                #                             model_request_dict['dep_args'][dep_id]['text_prompt'] = []
                #                         model_request_dict['dep_args'][dep_id]['text_prompt'].append(detools.download_file(file_value_fixed, get_file_content=True))
                #                     elif file_type in ['image', 'video', 'audio', 'file']:
                #                         try:
                #                             assert model_request_dict['dep_args'][dep_id][file_type]
                #                         except:
                #                             model_request_dict['dep_args'][dep_id][file_type] = []
                #                         model_request_dict['dep_args'][dep_id][file_type].append({
                #                             "file_name": str(file_value_fixed),
                #                             "file_url": f"{API_UP}/{file_value_fixed}"
                #                         })
                #                     else:
                #                         try:
                #                             assert model_request_dict['dep_args'][dep_id][file_type]
                #                         except:
                #                             model_request_dict['dep_args'][dep_id][file_type] = []
                #                         model_request_dict['dep_args'][dep_id][file_type].append(detools.download_file(file_value_fixed))
                                        
                #     cprint(f"Request DEP Files: {json.dumps(model_request_dict['dep_args'], indent=2)}", debug)
                    

                cprint("No Dependencies!", debug)    
                #exit()

            cprint(f"No task, wait..!", debug)   
            #exit()


            #model_request_dict["task_model"] = selected_model    # Return Model to work on

            if selected_task and "error" not in selected_task:
                break
        
        if not selected_task:
            cprint("Byeeee\n", debug)    
            return None

        model_request_dict["task_args"] = task_dic
        model_request_dict['task_id'] = selected_task['id']

        # send_task_data = {
        #    "api_key":self.user_api_key,
        #    "model":model
        # }
        # sendTask = simple_post(API_URL, data=send_task_data)
        
        return model_request_dict


    # Handle Model Service
    #   > Start Service
    def start_model_serv(self, model_id) -> None:
        _model_params = self.serv_conf["services_params"][model_id]
        
        #This code will make derunner NOT try to load a service if it is set to run constantly
        #because by default run constant model services will start with windows/linux os boot
        if not _model_params["submodel"] and CLI_MODE:
            if _model_params["run_constantly"]:
                return
        # MAYBE TODO:: Is to: make check service status, so 
            #if model service already running? 
        #        return
            #else:
            #| logic below will turn on service

        if not _model_params["submodel"]:
            _model_serv = self.serv_conf["services_params"][model_id][USER_SYS]
        else:
            _model_serv = self.serv_conf["services_params"][ _model_params["parent_model"] ][USER_SYS]

        _model_starter = os.path.join(USER_PATH, _model_serv["project_dir"], _model_serv["execs_path"], _model_serv["starter"]) if _model_serv["starter"] else None
        if not _model_starter:
            return
        
        if DEBUG or USER_SYS=="lin":
            start_cmd = ["bash", _model_starter] if USER_SYS=="lin" else [_model_starter]
            cprint(f'Model start cmd:\n\t{" ".join(start_cmd)}', DEBUG)
            _sproc = Popen(
                start_cmd
            )
        else:
            _sproc = Popen(
                [_model_starter],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        _sproc.wait()

        ret_code = _sproc.returncode
        if ret_code != 0:
            print(f"[ WARNING ] -> Something went wrong while attempting to start model service:\n\tmodel_name:{model_id}\n\tstarter_path:{_model_starter}\n\treturn code:{ret_code}")
            raise ChildProcessError(model_id)
        
        return
    
    #   > Stop Service 
    def stop_model_serv(self, model_id) -> None:
        _model_params = self.serv_conf["services_params"][model_id]

        if not _model_params["submodel"]:
            _model_params = self.serv_conf["services_params"][model_id]
        else:
            _model_params = self.serv_conf["services_params"][ _model_params["parent_model"] ]
        
        if _model_params["run_constantly"]:
            return
        
        _model_serv = _model_params[USER_SYS]

        _model_stoper = os.path.join(USER_PATH, _model_serv["project_dir"], _model_serv["execs_path"], _model_serv["stoper"]) if _model_serv["stoper"] else None
        if not _model_stoper:
            return None
        
        if DEBUG or USER_SYS=="lin":
            stop_cmd = ["bash", _model_stoper] if USER_SYS=="lin" else [_model_stoper]
            cprint(f'Model stop cmd:\n\t{" ".join(stop_cmd)}', DEBUG)
            _sproc = Popen(
                stop_cmd
            )
        else:
            _sproc = Popen(
                [_model_stoper],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        _sproc.wait()

        ret_code = _sproc.returncode
        if ret_code != 0:
            print(f"[ WARNING ] -> Something went wrong while attempting to stop model service:\n\tmodel_name:{model_id}\n\tstoper_path:{_model_stoper}\n\treturn code:{ret_code}")
            raise ChildProcessError(model_id)
        
        return


    # Services Upgrade Methods
    #   > Check if is time for upgrade
    def handle_upgrade_timer(self, create=False) -> str:
        if not os.path.isfile(LAST_UP_EPOCH) or create:
            cprint(f"[ TIMER DEBUG ] - MEMORY DOESN'T EXIST", False)
            with open(LAST_UP_EPOCH, "w") as fw:
                fw.write(str(time.time()))
            detools.user_chown(LAST_UP_EPOCH)
            return "go for it"
        
        cprint(f"[ TIMER DEBUG ] - MEMORY EXIST", DEBUG)
        with open(LAST_UP_EPOCH, "r") as fr:
            _last_up_ep = fr.read()
        _last_up_ep = float(_last_up_ep)
        detools.user_chown(LAST_UP_EPOCH)
        if time.time() - _last_up_ep >= UPG_FREQ:
            cprint(f"[ TIMER DEBUG ] - SECS PASSED SINCE LAST UPG = {int(time.time() - _last_up_ep)}", DEBUG)
            return "go for it"
        return None

    #   > Create Model(s) install script for reinstalation
    def create_model_reinstalation(self, model_ids, rm_models, submodel_critical_fail) -> str:
        # 1 - INIT + Scripts HEADER
        if USER_SYS == "win":
            '''I'm a windows nerd!'''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_install{int(time.time())}.bat")
            _start_cmd="start /W "
            _call = "call "
            _copy = "copy "
            _rm = "del "
            _noecho=" >NUL 2>NUL"
            _log_prefix = "ECHO Automatic.Reinstall - "
            _app_python = os.path.join(APP_PATH, "env", "python")
            # 1 - BAT HEADER
            _tmp_file_lines = ["@ECHO OFF\n"]
            
            # 1.1 - Wait DeRunner Service STOP
            if DERRUNER_ID in model_ids:
                derunner_status_path = os.path.join(APP_PATH, "executables", "Windows", "derunner.status.bat")
                _tmp_file_lines += [
                    ":wait_derunner_stop\n",
                    f'FOR /F "tokens=*" %%g IN (\'{derunner_status_path} /nopause\') do (SET derunner_status=%%g)\n',
                    "IF %derunner_status% EQU SERVICE_RUNNING GOTO wait_derunner_stop\n"
                ]
        elif USER_SYS=="lin":
            '''I know what i'm doing '''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_install{int(time.time())}.bash")
            _start_cmd="bash "
            _call=""
            _copy = "cp "
            _rm = "rm -rf "
            _noecho=" &>/dev/nul"
            _log_prefix = "echo Automatic.Reinstall - "
            _app_python = os.path.join(APP_PATH, "env", "bin", "python3")

             # 1 - BASH HEADER
            _tmp_file_lines = ["#!/bin/bash\n"]
            
            # 1.1 - Wait DeRunner Service STOP
            if DERRUNER_ID in model_ids:
                derunner_status_path = os.path.join(APP_PATH, "executables", "Linux", "derunner.status.bash")
                _tmp_file_lines += [
                    f"_serv_status=$(bash {derunner_status_path})\n",
                    'while [ "$_serv_status" = "SERVICE_RUNNING" ]\n',
                    "do\n",
                    f"\t_serv_status=$(bash {derunner_status_path})\n",
                    "done\n",
                ]

        if isinstance(model_ids, str):
            model_ids = [model_ids]
        
        if not isinstance(model_ids, list):
            return None
        
        # 2 - Uninstall <- Required Models
        if not submodel_critical_fail:
            for _model in model_ids:
                try:
                    _asset_sys_params=self.serv_conf["services_params"][_model][USER_SYS]
                    _asset_uninstaller = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["uninstaller"])
                except:
                    _asset_sys_params=self.last_serv_conf["services_params"][_model][USER_SYS]
                    _asset_uninstaller = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["uninstaller"])
                _uninstaller_bn = os.path.basename(_asset_uninstaller)
                _tmp_uninstaller = os.path.join(TMP_PATH, f'{int(time.time())}{_uninstaller_bn}')
                if os.path.isfile(_asset_uninstaller):
                    _tmp_file_lines += [
                        f"{_log_prefix}Uninstalling '{_model}'...>>{LOG_PATH}\n",
                        f"{_copy}{_asset_uninstaller} {_tmp_uninstaller}\n",
                        f'{_start_cmd}{_tmp_uninstaller} {" ".join(_asset_sys_params["uninstaller_args"] if "uninstaller_args" in _asset_sys_params and _asset_sys_params["uninstaller_args"] else [])}{f" /automatic {USER_PATH}" if USER_SYS=="win" else " -a" if USER_SYS=="lin" else ""}\n',
                        f'{_rm}{_tmp_uninstaller} {_noecho}\n'
                    ]

        # Remove Model from Service Configs
        _res_sconf, _ = self.get_services_config(ignore_update=True)
        cprint(f"[ UPGRADE ] -> pre services_configs: {json.dumps(_res_sconf, indent = 2)}", DEBUG)
        _compare_conf = _res_sconf.copy()
        for _model in rm_models:
            if _model in _compare_conf["services_params"]:
                _res_sconf["services_params"].pop(_model)
        cprint(f"[ UPGRADE ] -> pos services_configs: {json.dumps(_res_sconf, indent = 2)}", DEBUG)
        self.set_services_config(_res_sconf)

        if submodel_critical_fail:
            return None

        # 3 - Download + Uncompress to target folder <- Required Models
        for _count, _model in enumerate(model_ids):
            _asset_params=self.last_serv_conf["services_params"][_model]
            _asset_sys_params=_asset_params[USER_SYS]
            _asset_repo=_asset_params["source_code"]
            _asset_commit=_asset_sys_params["commit"]
            _asset_project_dir = os.path.join(USER_PATH, _asset_sys_params["install_dir"] if "install_dir" in _asset_sys_params else _asset_sys_params["project_dir"])
            _tmp_repo_dwnld_path=os.path.join(TMP_PATH, f"DeRunner_Dwnld_{_count}.zip")
            ## Download Commands
            if USER_SYS == "win":
                _mkdir="mkdir "
                _download_cmd=f'powershell -command "Invoke-WebRequest -Uri {_asset_repo}/archive/{_asset_commit}.zip -OutFile {_tmp_repo_dwnld_path}"\n'
                _uncompress_cmd=f'tar -xzvf {_tmp_repo_dwnld_path} -C {_asset_project_dir} --strip-components 1\n'
            elif USER_SYS=="lin":
                _mkdir="mkdir -p "
                _download_cmd=f'wget {_asset_repo}/archive/{_asset_commit}.zip -O {_tmp_repo_dwnld_path}\n'
                _uncompress_cmd=f'apt install libarchive-tools -y && bsdtar -xzvf {_tmp_repo_dwnld_path} -C {_asset_project_dir} --strip-components=1\n'
            _tmp_file_lines += [
                f"{_log_prefix}Downlading '{_model}'... >>{LOG_PATH}\n",
                f"{_mkdir}{_asset_project_dir}\n", # Create Asset Folder
                _download_cmd,
                _uncompress_cmd,
                f'{_rm}{_tmp_repo_dwnld_path} {_noecho}\n'
            ]


        # 4 - Setup <- Required Models
        for _model in model_ids:
            _asset_sys_params=self.last_serv_conf["services_params"][_model][USER_SYS]
            _asset_setup = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["setup"])
            _tmp_file_lines += [
                f"{_log_prefix}Installing '{_model}'... >>{LOG_PATH}\n",
                f'{_start_cmd}{_asset_setup} {" ".join(_asset_sys_params["setup_args"] if "setup_args" in _asset_sys_params and _asset_sys_params["setup_args"] else [])}\n'
            ]


        # 5 - Start `run_constantly` Models <- Required Models
        for _model in model_ids:
            _asset_params=self.last_serv_conf["services_params"][_model]
            _asset_sys_params=_asset_params[USER_SYS]
            if _model != DERRUNER_ID and _asset_params["run_constantly"]:
                _asset_start = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["starter"])
                _tmp_file_lines += [
                    f"{_log_prefix}Starting '{_model}'... >>{LOG_PATH}\n",
                    f'{_start_cmd}{_asset_start}\n'
                ]

            # 5.1 - Update user.config model
            _model_version=_asset_sys_params["version"]
            _new_model = json.dumps({
                _model: _model_version
            }).replace(" ", "").replace('"', '\\"')
            _manager_set_user_confs = os.path.join(APP_PATH, "Tools", "SetUserConfigs.py")
            _tmp_file_lines.append(f'{_call}{_app_python} {_manager_set_user_confs} --key models --value "{_new_model}"{_noecho}\n')
            # print(f'{_call}{_app_python} {_manager_set_user_confs} --key models --value "{_new_model}"{_noecho}\n')
        
    
        ## 5.1 - after asset instalation!!
        #   > Update Services Config with params from Latest Services Config
        _app_after_model_reinstall = os.path.join(APP_PATH, "Tools", "after_model_reinstall.py")
        _tmp_file_lines.append(f'{_call}{_app_python} {_app_after_model_reinstall}{_noecho}\n')
        cprint(f'{_call}{_app_python} {_app_after_model_reinstall}{_noecho}\n', DEBUG)
        # delogger(f'{_call}{_app_python} {_app_after_model_reinstall}{_noecho}\n')


        # Force DeRunner Restart
        _asset_sys_params=self.last_serv_conf["services_params"][DERRUNER_ID][USER_SYS]
        _derunner_start = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["starter"])
        _tmp_file_lines += [
            f"{_log_prefix}Force Start DeRunner >>{LOG_PATH}\n",
            f'{_start_cmd}{_derunner_start}\n'
        ]


        ## END OF FILE - Delete Bat at end of instalation 
        ### WINDOWS - retrieved from https://stackoverflow.com/a/20333152
        ### LINUX   - ...
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n'if USER_SYS == "win" else f'rm -rf {target_path}\n' if USER_SYS == "lin" else "")


        # 6 - Create Installer File
        with open(target_path, "w") as fw:
            fw.writelines(_tmp_file_lines)
        detools.user_chown(target_path)
        return target_path

    #   > Request Model(s) reinstalation
    def request_model_reinstall(self, reinstall_models, init=False) -> bool:
        '''
        Exit Codes:
        10 - Submodel Critical Fail
         9 - Reinstall Fail

         2 - Reinstall Started W DeRunner
         1 - Reinstall Started W/O DeRunner (Not Required to Stop Services)
         0 - No Model to re-install
        '''
        if init:
            # UPGRADE CONFIGURATIONS (Target: self.last_serv_conf)
            self.__init__()

        if isinstance(reinstall_models, str):
            reinstall_models = [reinstall_models]
        if not isinstance(reinstall_models, list):
            return 9
        
        # Remove Model from User Configs && Get to know Current pass come from submodel critical_fail
        #   - Prevent models being called by DeRunner
        #   - Garantee Models are tested after reinstall
        _res_uconf = self.get_user_config()
        _compare_conf = _res_uconf.copy()
        _total_rm_serv = []
        submodel_critical_fail = False
        for _model in reinstall_models:
            try:
                model_params = self.serv_conf['services_params'][_model]
            except:
                model_params = self.last_serv_conf['services_params'][_model]
            try: # Rem from models
                _total_rm_serv.append(_model)
                # edit user config models
                if model_params["submodel"]:
                    if model_params["parent_model"] in reinstall_models:
                        continue
                    else:
                        # I believe this will only happen in Critical Fail
                        submodel_critical_fail = True
                        _model = model_params["parent_model"]
                else:
                    submodel_critical_fail = False
                if _model in _compare_conf["models"]:
                    _res_uconf["models"].pop(_model)
            except:
                pass
            try: # Search Childs
                _childs = _compare_conf["child_models"] if _compare_conf["child_models"] else []
                for c in _childs:
                    if c in _compare_conf["models"]:
                        _res_uconf["models"].pop(c)
                        _total_rm_serv.append(c)
            except:
                pass
            try: # Rem from admissions
                print("[ UPGRADE ] Model Group:", json.dumps(_total_rm_serv, indent = 2))
                # edit user config admissions
                if "admissions" in _compare_conf and _compare_conf["admissions"]:
                    for un_mo_ch in _total_rm_serv:
                        for admn_key, admissions in _compare_conf["admissions"].items():
                            if un_mo_ch in admissions:
                                _res_uconf["admissions"][admn_key].pop(un_mo_ch)
            except:
                pass
        
        if submodel_critical_fail: # Re-Install Fail - Uninstall Model!!
            _res_uconf = _compare_conf.copy()
            cprint(f"[ UPGRADE ] -> pre user_configs: {json.dumps(_res_uconf, indent = 2)}", DEBUG)
            try:
                # REM admissions from user configs 
                if "admissions" in _compare_conf and _compare_conf["admissions"]:
                    for _model in reinstall_models:
                        for admn_key, admissions in _compare_conf["admissions"].items():
                            if _model in admissions:
                                _res_uconf["admissions"][admn_key].pop(_model)
            except:
                pass
            self.set_user_config(_res_uconf)
            return 10

        self.set_user_config(_res_uconf)

        # Generate Reinstall Script
        self.__init__(ignore_update=True)
        _reinstall_path = self.create_model_reinstalation(reinstall_models, _total_rm_serv, submodel_critical_fail)
        if not _reinstall_path:
            return 9

        # os.spawnl(os.P_OVERLAY, str(_reinstall_path), )

        # retrieved from https://stackoverflow.com/a/14797454
        if USER_SYS == "win":
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008
            _reinstall_cmd = [_reinstall_path]
            # TODO: https://stackoverflow.com/a/13256908
            Popen(
                _reinstall_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            )
        elif USER_SYS == "lin":
            _reinstall_cmd = ['/bin/bash', _reinstall_path]  
            # inspired in https://stackoverflow.com/a/60280256
            subprocess.Popen(
                _reinstall_cmd,
                stdout=None, 
                stderr=None,
                universal_newlines=True,
                preexec_fn=os.setpgrp 
            )
        print(f" [ WARNING ] -> Model(s) Reinstalation Requested:\n\tmodel: {reinstall_models}\n\treinstall cmd: {' '.join(_reinstall_cmd)}")
        if DERRUNER_ID in reinstall_models:
            return 2
        return 1
    
    #   > Create Model(s) uninstall script for uninstalation
    def create_model_uninstalation(self, model_ids, rm_models) -> str:
        # 1 - INIT + Scripts HEADER
        if USER_SYS == "win":
            '''I'm a windows nerd!'''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_uninstall{int(time.time())}.bat")
            _start_cmd="start /W "
            _call = "call "
            _copy = "copy "
            _rm = "del "
            _noecho=" >NUL 2>NUL"
            _log_prefix = "ECHO DeRunner.Uninstall - "
            _app_python = os.path.join(APP_PATH, "env", "python")
            # 1 - BAT HEADER
            _tmp_file_lines = ["@ECHO OFF\n"]
            
            # 1.1 - Wait DeRunner Service STOP
            if DERRUNER_ID in model_ids:
                derunner_status_path = os.path.join(APP_PATH, "executables", "Windows", "derunner.status.bat")
                _tmp_file_lines += [
                    ":wait_derunner_stop\n",
                    f'FOR /F "tokens=*" %%g IN (\'{derunner_status_path} /nopause\') do (SET derunner_status=%%g)\n',
                    "IF %derunner_status% EQU SERVICE_RUNNING GOTO wait_derunner_stop\n"
                ]
        elif USER_SYS=="lin":
            '''I know what i'm doing '''
            # Init
            target_path = os.path.join(TMP_PATH, f"tmp_model_uninstall{int(time.time())}.bash")
            _start_cmd="bash "
            _call=""
            _copy = "cp "
            _rm = "rm -rf "
            _noecho=" &>/dev/nul"
            _log_prefix = "echo DeRunner.Uninstall - "
            _app_python = os.path.join(APP_PATH, "env", "bin", "python3")

             # 1 - BASH HEADER
            _tmp_file_lines = ["#!/bin/bash\n"]
            
            # 1.1 - Wait DeRunner Service STOP
            if DERRUNER_ID in model_ids:
                derunner_status_path = os.path.join(APP_PATH, "executables", "Linux", "derunner.status.bash")
                _tmp_file_lines += [
                    f"_serv_status=$(bash {derunner_status_path})\n",
                    'while [ "$_serv_status" = "SERVICE_RUNNING" ]\n',
                    "do\n",
                    f"\t_serv_status=$(bash {derunner_status_path})\n",
                    "done\n",
                ]

        if isinstance(model_ids, str):
            model_ids = [model_ids]
        if not isinstance(model_ids, list):
            return None
        
        # 2 - Uninstall <- Required Models
        if not DEVELOPMENT:
            for _model in model_ids:
                _asset_sys_params=self.serv_conf["services_params"][_model][USER_SYS]
                _asset_uninstaller = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["uninstaller"])
                _uninstaller_bn = os.path.basename(_asset_uninstaller)
                _tmp_uninstaller = os.path.join(TMP_PATH, f'{int(time.time())}{_uninstaller_bn}')
                if os.path.isfile(_asset_uninstaller):
                    _tmp_file_lines += [
                        f"{_log_prefix}Uninstalling '{_model}'...>>{LOG_PATH}\n",
                        f"{_copy}{_asset_uninstaller} {_tmp_uninstaller}\n",
                        f'{_start_cmd}{_tmp_uninstaller} {" ".join(_asset_sys_params["uninstaller_args"] if "uninstaller_args" in _asset_sys_params and _asset_sys_params["uninstaller_args"] else [])}{f" /automatic {USER_PATH}" if USER_SYS=="win" else " -a" if USER_SYS=="lin" else ""}\n',
                        f'{_rm}{_tmp_uninstaller} {_noecho}\n'
                    ]

        # Remove Model from Service Configs
        _res_sconf, _ = self.get_services_config(ignore_update=True)
        _compare_conf = _res_sconf.copy()
        for _model in rm_models:
            if _model in _compare_conf["services_params"]:
                _res_sconf["services_params"].pop(_model)
        self.set_services_config(_res_sconf)
        if DEVELOPMENT:
            return "devop"
        
        # Force DeRunner Restart
        _asset_sys_params=self.last_serv_conf["services_params"][DERRUNER_ID][USER_SYS]
        _derunner_start = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["starter"])
        _tmp_file_lines += [
            f"{_log_prefix}Force Start DeRunner >>{LOG_PATH}\n",
            f'{_start_cmd}{_derunner_start}\n'
        ]


        ## END OF FILE - Delete Bat at end of instalation 
        ### WINDOWS - retrieved from https://stackoverflow.com/a/20333152
        ### LINUX   - ...
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n'if USER_SYS == "win" else f'rm -rf {target_path}\n' if USER_SYS == "lin" else "")


        # 6 - Create Uninstaller File
        with open(target_path, "w") as fw:
            fw.writelines(_tmp_file_lines)
        detools.user_chown(target_path)
        return target_path

    #   > Request Model(s) uninstalation
    def request_model_uninstall(self, uninstall_models) -> bool:
        '''
        Exit Codes:
        1 - Uninstall Started W/O DeRunner (Not Required to Stop Services)
        2 - Uninstall Started W DeRunner
        8 - Development Mode (Update Configs only)
        9 - Uninstall Fail
        '''

        if isinstance(uninstall_models, str):
            uninstall_models = [uninstall_models]
        if not isinstance(uninstall_models, list):
            return 9
            
        # Remove Model from User Configs
        #   - Prevent models being called by DeRunner
        _res_uconf = self.get_user_config()
        _compare_conf = _res_uconf.copy()
        _total_rm_serv = []
        submodel_list=[]
        for _model in uninstall_models:
            is_submodel = False
            try:
                model_params = self.serv_conf['services_params'][_model]
            except:
                model_params = self.last_serv_conf['services_params'][_model]
            try: # Rem from models
                _total_rm_serv.append(_model)
                if model_params["submodel"]:
                    is_submodel = True
                    submodel_list.append(True)
                else:
                    submodel_list.append(False)
                # edit user config models
                if _model in _compare_conf["models"]:
                    _res_uconf["models"].pop(_model)
            except:
                pass
            try: # Search Childs
                if not is_submodel:
                    _childs = _compare_conf["child_models"] if _compare_conf["child_models"] else []
                    for c in _childs:
                        if c in _compare_conf["models"]:
                            _res_uconf["models"].pop(c)
                            _total_rm_serv.append(c)
            except:
                pass
            try: # Rem from admissions
                print("[ UNINSTALL ] Model Group:", json.dumps(_total_rm_serv, indent = 2))
                # edit user config admissions
                if "admissions" in _compare_conf and _compare_conf["admissions"]:
                    for un_mo_ch in _total_rm_serv:
                        for admn_key, admissions in _compare_conf["admissions"].items():
                            if un_mo_ch in admissions:
                                _res_uconf["admissions"][admn_key].pop(un_mo_ch)
            except:
                pass
        cprint(f"[ UNINSTALL ] -> pre user_configs: {json.dumps(_res_uconf, indent = 2)}", DEBUG)
        self.set_user_config(_res_uconf)

        if len(submodel_list) < 1:
            return 9
        if not False in submodel_list:
            return 1

        # Generate Reinstall Script
        self.__init__(ignore_update=True)
        _uninstall_path = self.create_model_uninstalation(uninstall_models, _total_rm_serv)
        if _uninstall_path == "devop":
            return 8
        elif not _uninstall_path:
            return 9

        # os.spawnl(os.P_OVERLAY, str(_uninstall_path), )

        # retrieved from https://stackoverflow.com/a/14797454
        if USER_SYS == "win":
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008
            _uninstall_cmd = [_uninstall_path]
            # TODO: https://stackoverflow.com/a/13256908
            Popen(
                _uninstall_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            )
        elif USER_SYS == "lin":
            _uninstall_cmd = ['/bin/bash', _uninstall_path]  
            # inspired in https://stackoverflow.com/a/60280256
            subprocess.Popen(
                _uninstall_cmd,
                stdout=None, 
                stderr=None,
                universal_newlines=True,
                preexec_fn=os.setpgrp 
            )
        print(f" [ WARNING ] -> Model(s) Uninstalation Requested:\n\tmodel: {uninstall_models}\n\tuninstall cmd: {' '.join(_uninstall_cmd)}")
        if DERRUNER_ID in uninstall_models:
            return 2
        return 1
    
    #   > Check for upgrades
    def req_service_upgrade(self):
        '''
        Exit Codes:
        9 - Upgrade Fail

        2 - Upgrade Started W DeRunner
        1 - Upgrade Started W/O DeRunner (Not Required to Stop Services)
        0 - No Model to Upgrade
        '''
        if DEVELOPMENT:
            return 0
        # Timer check
        upgrade_timer = self.handle_upgrade_timer()
        if upgrade_timer != "go for it":
            return 0
        

        delogger(f"[ INFO:{int(time.time())} ] - Searching for models upgrade.")
        print(f"[ INFO:{int(time.time())} ] - Searching for models upgrade.")
        # UPGRADE CONFIGURATIONS (Target: self.last_serv_conf)
        self.__init__()
        user_models = self.user_models
        try:
            assert self.user_conf["quarantine"]
            for q_model in self.user_conf["quarantine"]:
                user_models[q_model] = self.user_conf["quarantine"][q_model]
        except: pass
        print("[ INFO ] -> UPG MODELS: ", json.dumps(user_models, indent=2))
        if not user_models:
            delogger(f"[ UPGRADE ] - No model found. Next upgrade in {int(UPG_FREQ/3600)}h")
            print(f"[ UPGRADE ] - No model found. Next upgrade in {int(UPG_FREQ/3600)}h")
            return 0
        _upg_models = []
        for _model in list(user_models.keys()):
            if self.serv_conf["services_params"][_model]["submodel"]:
                continue
            curr_version = self.serv_conf["services_params"][_model][USER_SYS]["version"]
            last_version = self.last_serv_conf["services_params"][_model][USER_SYS]["version"]
            if curr_version != last_version:
                _upg_models.append(_model)
        self.handle_upgrade_timer(create=True)
        if not _upg_models:
            delogger(f"[ UPGRADE ] - Up to date. Next upgrade in {int(UPG_FREQ/3600)}h")
            print(f"[ UPGRADE ] - Up to date. Next upgrade in {int(UPG_FREQ/3600)}h")
            return 0
        delogger(f"[ INFO:{int(time.time())} ] - Founded the following models to upgrade: {_upg_models}")
        print(f"[ INFO:{int(time.time())} ] - Founded the following models to upgrade: {_upg_models}")
        req_reinstall = self.request_model_reinstall(_upg_models)
        if req_reinstall != 9:
            self.handle_upgrade_timer(create=True)
        return req_reinstall

    #   > Test Models Funks
    def quiet_subprocess(self, cmd_list, timeout=None):
        start_time = time.time()
        # retrieved from https://stackoverflow.com/a/62226026
        if USER_SYS == "lin":
            cprint(f'Quiet Subprocess Requested:\n\t{" ".join(cmd_list)}', DEBUG)
            _sproc = Popen(
                cmd_list
            )
        elif USER_SYS == "win":                
            _sproc = Popen(
                cmd_list,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            return 1
        while True:
            if timeout and time.time() - start_time > timeout:
                return 1
            ret_code = _sproc.poll()
            if ret_code != None:
                break
            continue
        return ret_code
        
    def grab_models2test(self):
        # Grab Function required Configs
        user_config = self.get_user_config()
        mem_user_config = self.get_user_config()
        user_models = self.grab_runner_models()
        try:
            user_key = user_config["api_key"]
        except:
            return {}, {}
        user_update = False
        if not user_models or not user_key:
            return {}, {}

        # Confirm if user_config has admissions key
        if "admissions" not in user_config:
            user_config["admissions"] = {}
            self.set_user_config(user_config)
        if user_key not in user_config["admissions"]:
            user_config["admissions"][user_key] = {}
            self.set_user_config(user_config)

        models2test = {}
        models_tested = []
        for model in user_models:
            try:
                version = user_config["models"][model]
            except:
                continue
            if model in user_config["admissions"][user_key] and user_config["admissions"][user_key][model] == version:
                models_tested.append(model)
                continue

            # Confirm if model have been allready tested
            if user_config["admissions"]:
                for ak, tm in user_config["admissions"].items():
                    if isinstance(tm, dict) and model in tm:
                        if tm[model] != version:
                            user_config["admissions"][ak].pop(model)
                        else:
                            # Model have been tested with other api_key
                            user_config["admissions"][user_key][model] = version
                            # DeSOTA API ADD MODEL to this API
                            _add_model_payload = {
                                "api_key": user_key,
                                "models_list": model,
                                "add_model": "1"
                            }
                            delogger([
                                f"[ API Append Model ]\n",
                                f"       model: {model}:\n", 
                                f"        url: {API_URL}:\n", 
                                f"    payload: {json.dumps(_add_model_payload, indent=2)}\n",
                            ])

                            _add_service_res = simple_post(url = API_URL, data = _add_model_payload)
                            
                            delogger([
                                f"    response: {_add_service_res.text}\n",
                                f"      result: {_add_service_res}\n"
                            ])
                        self.set_user_config(user_config)
            # Final Own API Admission Confirmation
            if model in user_config["admissions"][user_key] and user_config["admissions"][user_key][model] == version:
                models_tested.append(model)
                continue
            else:
                models2test[model] = version
        return models2test, models_tested
    
    def test_models(self, in_models=None):
        if isinstance(in_models, str):
            in_models = [in_models]
        # Monitor newby models to test
        models2test, models_tested = self.grab_models2test()
        if in_models != None:
            models2test = {}
            user_config = self.get_user_config()
            for in_model in in_models:
                try:
                    assert user_config["models"][in_model]
                except:
                    continue
                models2test[in_model] = user_config["models"][in_model]
        # If no Model Found
        if not models2test:
            return models_tested

        # Test Models Logic Bellow
        test_script_path = os.path.join(APP_PATH, "Tools", "builtin_model_tester.py")
        for model, version in models2test.items():
            # INFO
            print(f"[ INFO ] -> Model Tester start:\n  Model ID: {model}")
            delogger(f"[ INFO ] -> Model Tester start:\n  Model ID: {model}")

            # Get Model Test TimeOut
            try: # from service ~ test_timeout
                assert self.serv_conf["services_params"][model][USER_SYS]["test_args"]["test_timout"]
                model_test_timeout = self.serv_conf["services_params"][model][USER_SYS]["test_args"]["test_timout"]
            except:
                try: # from service ~ timeout
                    assert self.serv_conf["services_params"][model]["timout"]
                    model_test_timeout = self.serv_conf["services_params"][model]["timout"]
                except:
                    try: # from latest_service ~ test_timeout
                        assert self.last_serv_conf["services_params"][model][USER_SYS]["test_args"]["test_timout"]
                        model_test_timeout = self.last_serv_conf["services_params"][model][USER_SYS]["test_args"]["test_timout"]
                    except:
                        try: # from latest_service ~ timeout
                            assert self.last_serv_conf["services_params"][model]["timout"]
                            model_test_timeout = self.last_serv_conf["services_params"][model]["timout"]
                        except:
                            model_test_timeout = DEFAULT_MODEL_TIMEOUT
            
            # Get Model Test CMD
            model_test_cmd = ['--model', model]
            model_test_cmd = [self.pypath, test_script_path] + model_test_cmd
            print(f"[ INFO ] Model Test CMD ({model}):", " ".join(model_test_cmd))
            delogger(f"[ INFO ] Model Test CMD ({model}): {' '.join(model_test_cmd)}")

            test_res = self.quiet_subprocess(model_test_cmd, model_test_timeout)
            if test_res == 0:
                self.__init__(ignore_update=True)
                user_conf = self.user_conf
                user_conf["admissions"][self.user_api_key].update({model:version})
                self.set_user_config(user_conf)
                models_tested.append(model)
                print(f"[ INFO ] -> Model Tester end:\n  Model ID: {model}\n  Result: SUCCESS")
                delogger(f"[ INFO ] -> Model Tester end:\n  Model ID: {model}\n  Result: SUCCESS")
                # print("TEST: ", API_URL + f"?api_key={self.user_api_key}&models_list={uninstalled_model}&remove_model=1")
                _add_model_payload = {
                    "api_key": self.user_api_key,
                    "models_list": model,
                    "add_model": "1"
                }
                delogger([
                    f"[ API Append Model ]\n",
                    f"       model: {model}:\n", 
                    f"        url: {API_URL}:\n", 
                    f"    payload: {json.dumps(_add_model_payload, indent=2)}\n",
                ])

                _add_service_res = simple_post(url = API_URL, data = _add_model_payload)
                
                delogger([
                    f"    response: {_add_service_res.text}\n",
                    f"      result: {_add_service_res}\n"
                ])
            elif not DEVELOPMENT:
                # CRITICAL FAILURE
                self.add_quarantine_model(model)
                req_uninstall = self.request_model_uninstall(model)
                
                # DeRunner Uninstall Requested
                if req_uninstall == 2:
                    # STOP SERVICE
                    exit(66)
                
                # DeSOTA API REMOVE MODEL
                # print("TEST: ", DESOTA_API_URL + f"?api_key={self.user_api_key}&models_list={model}&remove_model=1")
                _rem_service_payload = {
                    "api_key": self.user_api_key,
                    "models_list": model,
                    "remove_model": "1"
                }
                delogger([
                    f"[ API Append Model ]\n",
                    f"       model: {model}:\n", 
                    f"        url: {API_URL}:\n", 
                    f"    payload: {json.dumps(_rem_service_payload, indent=2)}\n",
                ])
                
                _rem_service_res = simple_post(url = API_URL, data = _rem_service_payload)

                delogger([
                    f"    response: {_rem_service_res.text}\n",
                    f"      result: {_rem_service_res}\n"
                ])
                
                print(f"[ INFO ] -> Model Tester end:\n  Model ID: {model}\n  Result: FAIL")
                delogger(f"[ INFO ] -> Model Tester end:\n  Model ID: {model}\n  Result: FAIL")
        
        return models_tested


    # Call Model Runner
    def call_model(self, model_req):
        '''
        return codes:
        - 0 (sucess)
        - 1 (input error)
        - 2 (output error / timeout)
        - 3 (desota comunication error)
        - _ (critical fail) # causes model automatic reinstall
        '''
        signal_api_freq = 60 # seconds
        start_time = time.time()
        request_creation_timeout = 60
        # Create tmp model_req.yaml with request params for model runner
        _tmp_req_path = os.path.join(TMP_PATH, f"tmp_model_req{int(time.time())}.yaml")
        with open(_tmp_req_path, 'w',) as fw:
            yaml.dump(model_req,fw,sort_keys=False)
        while not os.path.exists(_tmp_req_path):
            if time.time() - start_time > request_creation_timeout:
                return 1
            time.sleep(1)
        last_signal_time = start_time
        # Model Vars
        _model_id = model_req['task_model']                                             # Model Name
        _model_runner_param = self.serv_conf["services_params"][_model_id]  # Model params from services.config.yaml
        _model_runner_sys_param = _model_runner_param[USER_SYS] 
        _model_runner_py = None
        _model_isTool = (_model_runner_param["service_type"] == "tool")
        if str(_model_runner_sys_param["desota_runner"]).endswith(".py"):
            _model_runner = os.path.join(USER_PATH, _model_runner_sys_param["project_dir"], _model_runner_sys_param["desota_runner"])          # Model runner path
            _model_runner_py = os.path.join(USER_PATH, _model_runner_sys_param["python_path"])    # Python with model runner packages
        if str(_model_runner_sys_param["desota_runner"]).endswith(".bat"):
            _model_runner = os.path.join(USER_PATH, _model_runner_sys_param["desota_runner"])          # Model runner path
            
        # API Response URL
        _model_res_url = f"{API_URL}?api_key={self.user_api_key}&model={model_req['task_model']}&send_task=" + model_req['task_id']
        # Begin and Wait Model
        # retrieved from https://stackoverflow.com/a/62226026
        if not _model_runner_py:
            _modelCall_cmd = [
                _model_runner, 
                "--model_req", _tmp_req_path, 
                f'--model_res_url="{_model_res_url}"'
            ]
            print(" [ DEBUG ] -> GOing to run:", " ".join(_modelCall_cmd))
            model_running_payload = {
                        "api_key": self.user_api_key,
                        "models_list": _model_id,
                        "handshake":"1"
                    }
            model_running_res = simple_post(url=API_URL, data=model_running_payload)
            try:
                _sproc = check_call(
                    _modelCall_cmd
                )
                _ret_code = 0
            except CalledProcessError as e:
                _ret_code = e
        else:
            _modelCall_cmd = [
                _model_runner_py, _model_runner, 
                "--model_req", _tmp_req_path, 
                "--model_res_url", _model_res_url
            ]
        
            # Start / Wait Model
            # retrieved from https://stackoverflow.com/a/62226026
            cprint(f'[ INFO ] Model runner cmd:\n\t{" ".join([_model_runner_py, _model_runner, "--model_req", _tmp_req_path, "--model_res_url", _model_res_url])}', DEBUG)
            if _model_isTool:
                _sproc = Popen(
                    _modelCall_cmd,
                    #stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE, 
                    stderr=None if CLI_MODE else subprocess.PIPE, 
                    encoding='utf-8',
                )
            else:
                _sproc = Popen(
                    _modelCall_cmd
                )
            # Model timeout
            try:
                _model_runner_timeout = _model_runner_param["timeout"]
            except:
                _model_runner_timeout = DEFAULT_MODEL_TIMEOUT
            print(" [ DEBUG ] -> Model Timeout:", _model_runner_timeout)
            # Signal User Configs
            edit_user_conf = self.get_user_config()
            try:
                edit_user_conf["running"][self.user_api_key] = _model_id
            except:
                edit_user_conf.update({"running":{self.user_api_key:_model_id}})
            self.set_user_config(edit_user_conf)

            # Lets GO!
            while True:
                # Check Timeout
                if time.time() - start_time > _model_runner_timeout:
                    _ret_code = 2
                    break
                _ret_code = _sproc.poll()
                if _ret_code != None:
                    break
                # Signal DeSOTA API
                if time.time() - last_signal_time > signal_api_freq:
                    last_signal_time = time.time()
                    model_running_payload = {
                        "api_key": self.user_api_key,
                        "models_list": _model_id,
                        "handshake":"1"
                    }
                    model_running_res = simple_post(url=API_URL, data=model_running_payload)
                    cprint(f"[ INFO ] -> Signal Desota about Server Alive: {json.dumps(model_running_res.json(), indent=2)}", DEBUG)
                continue

        # Remove Signal from User Configs
        edit_user_conf["running"][self.user_api_key] = None
        self.set_user_config(edit_user_conf)
        
        if os.path.isfile(_tmp_req_path):
            os.remove(_tmp_req_path)

        print(f"[ INFO ] -> Model `{model_req['task_model']}` returncode = {_ret_code}")
        delogger(f"[ INFO ] -> Model `{model_req['task_model']}` returncode = {_ret_code}")
        
        return _ret_code


    # Main DeRunner Loop
    def mainloop(self) -> None:
        # Print Configurations
        print("Runner Up!")
        delogger("Runner Up!")
        
        print(f"[ INFO ] -> Configurations:\n{json.dumps(self.user_conf, indent=2)}")
        delogger(f"[ INFO ] -> Configurations:\n{json.dumps(self.user_conf, indent=2)}")
        
        _reinstall_model = None
        while True:
            # Check Service Stop Request
            check_status()
            try:
                # Check for model upgrades
                req_serv_upg = self.req_service_upgrade()
                # DeRunner Upgrade Requested
                if req_serv_upg == 2:
                    # STOP SERVICE
                    exit(66)
                check_status()

                # Check for untested models
                admmit_models = self.test_models()
                check_status()

                model_req = self.monitor_model_request(admmit_models, debug=DEBUG)
                check_status()
                if not model_req:
                    continue
                print("*"*80)
                delogger("*"*80)
                print(f"[ INFO ] -> Incoming Model Request:\n{json.dumps(model_req, indent=2)}")
                delogger(f"[ INFO ] -> Incoming Model Request:\n{json.dumps(model_req, indent=2)}")

                self.start_model_serv(model_req['task_model'])
                
                model_res = self.call_model(model_req)
                
                error_level = None
                if model_res == 1:
                    print(f"[ ERROR ] -> Model INPUT ERROR (Write exec_state = 9)")
                    error_level = 9
                    error_msg = "Model INPUT ERROR"
                elif model_res == 2:
                    print(f"[ ERROR ] -> Model OUTPUT ERROR (Retry in another server)")
                    error_level = 8
                    error_msg = "Model OUTPUT ERROR"
                elif model_res == 3:
                    print(f"[ ERROR ] -> Write Result to DeSOTA ERROR (Retry in another server)")
                    error_level = 8
                    error_msg = "Write Result to DeSOTA ERROR"
                elif model_res != 0:
                    raise ChildProcessError(model_req['task_model'])
                
                self.stop_model_serv(model_req['task_model'])

                _reinstall_model = None

            except ChildProcessError as cpe:
                #cpe = model name
                # Inform DeSOTA API that this server can no longer continue this request!
                print(f"[ WARNING ] -> Re-Install Model in background: {cpe}")
                delogger(f"[ WARNING ] -> Re-Install Model in background: {cpe}")
                error_level = 8
                error_msg = f"Model CRITICAL ERROR: {cpe}"
                _reinstall_model = str(cpe)
                pass
            except Exception as e:
                print(f'[ CRITICAL FAIL ] -> DeRunner Fail INFO:\n  Exception: {e}\n  {traceback.format_exc()}')
                delogger([
                    f"[ CRITICAL FAIL ] -> Re-Install DeRunner: \n",
                    f"  Exception: {e}\n",
                    f"  {traceback.format_exc()}\n"
                ])
                error_level = 8
                error_msg = f"DeRunner CRITICAL FAIL"
                # > Something to think about Pos Beta-Release:
                # > _reinstall_model is now on treated as a model to Re-Test, derunner cannot test itself...
                # if not DEVELOPMENT:
                #     _reinstall_model = DERRUNER_ID
                pass

            if error_level and not DEBUG:
                _handled_error = True
                try: # If error_level without some payload parameter 
                    error_payload = {
                        "api_key": self.user_api_key,
                        "model": model_req['task_model'],
                        "send_task": model_req['task_id'],
                        "error": error_level,
                        "error_msg": error_msg
                    }
                except:
                    _handled_error = False
                    delogger(f"[ WARNING ] -> DeSOTA Unhandled Error")

                if _handled_error:
                    _rem_service_res = simple_post(url=API_URL, data=error_payload)
                    print(f"[ INFO ] -> DeSOTA ERROR Upload:\n\tURL: {API_URL}\n\tRES: {json.dumps(_rem_service_res.json(), indent=2)}")
                    delogger(f"[ INFO ] -> DeSOTA ERROR Upload:\n\tURL: {API_URL}\n\tRES: {json.dumps(_rem_service_res.json(), indent=2)}")
                    time.sleep(.8)
            
            if _reinstall_model:
                admmit_models = self.test_models([_reinstall_model])
                if _reinstall_model in admmit_models:
                    log = f"[ INFO ] -> Model [{_reinstall_model}] Re-Admited"
                else:
                    log = f"[ WARNING ] -> Model [{_reinstall_model}] Uninstalled after failure!"
                print(log)
                delogger(log)

if __name__ == "__main__":
    # Check Service Stop Request
    check_status()
    
    # Start DeRunner
    derunner_class = Derunner() # init
    derunner_class.mainloop()
