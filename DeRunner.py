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

I=0
DEBUG = False
DEVELOPMENT = False
if len(sys.argv)>1:
    if sys.argv[1] in ["-dev"]:
        DEVELOPMENT = True
    elif sys.argv[1] in ["-deb"]:
        DEBUG = True

# inspired inhttps://stackoverflow.com/a/13874620
def get_platform():
    _platform = sys.platform
    _win_res=["win32", "cygwin", "msys"]
    _lin_res=["linux", "linux2"]
    _user_sys = "win" if _platform in _win_res else "lin" if _platform in _lin_res else None
    if not _user_sys:
        raise EnvironmentError(f"Plataform `{_platform}` can not be parsed to DeSOTA Options: Windows={_win_res}; Linux={_lin_res}")
    return _user_sys
USER_SYS=get_platform()
    
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
def user_chown(path):
    '''Remove root previleges for files and folders: Required for Linux'''
    if USER_SYS == "lin":
        #CURR_PATH=/home/[USER]/Desota/DeRunner
        os.system(f"chown -R {USER} {path}")
    return
    
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
LOG_PATH = os.path.join(DESOTA_ROOT_PATH, "demanager.log")
TMP_PATH=os.path.join(DESOTA_ROOT_PATH, "tmp")
if not os.path.isdir(TMP_PATH):
    os.mkdir(TMP_PATH)
    user_chown(TMP_PATH)

CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
if not os.path.isdir(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)
    user_chown(CONFIG_PATH)
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
    user_chown(LOG_PATH)
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
# Downld Desota Files
def get_url_from_str(string):
    # retrieved from https://www.geeksforgeeks.org/python-check-url-string/
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]
#
def retrieve_file_content(file_idx):
    if os.path.isfile(file_idx):
            with open(file_idx, 'r') as fr:
                return fr.read()
    file_url = get_url_from_str(file_idx)
    file_ext = os.path.splitext(file_url)[1] if file_url else None
    if not file_url or not file_ext:
        return file_idx
    file_content = ""

    _http_connect = True
    while True:
        try:
            with  requests.get(file_idx, stream=True) as req_file:
                if req_file.status_code != 200:
                    return file_idx
                
                if req_file.encoding is None:
                    req_file.encoding = 'utf-8'

                for line in req_file.iter_lines(decode_unicode=True):
                    if line:
                        file_content += line
            break
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
    if not _http_connect:
        print(f"[ INFO ] -> DeRunner Internet Acess Re-Established")
        delogger(f"[ INFO ] -> DeRunner Internet Acess Re-Established")
    return file_content
#
def download_file(file_idx, get_file_content=False) -> str:
    if get_file_content:
        return retrieve_file_content(file_idx)
    out_path = os.path.join(TMP_PATH, os.path.basename(file_idx))
    if os.path.isfile(file_idx):
        return file_idx
    file_url = get_url_from_str(file_idx)[0]
    file_ext = os.path.splitext(file_url)[1] if file_url else None
    if not file_url or not file_ext:
        return file_idx

    _http_connect = True
    while True:
        try:
            with requests.get(file_idx, stream=True) as r:
                if r.status_code != 200:
                    return file_idx
                with open(out_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                break
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
    if not _http_connect:
        print(f"[ INFO ] -> DeRunner Internet Acess Re-Established")
        delogger(f"[ INFO ] -> DeRunner Internet Acess Re-Established")

    return out_path
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
        exit(0)


# DeRunner Class
class Derunner():
    # Configurations
    def __init__(self, ignore_update=False) -> None:
        self.serv_conf, self.last_serv_conf = self.get_services_config(ignore_update=ignore_update)
        self.user_conf = self.get_user_config()
        self.user_models = self.user_conf['models']
        self.user_api_key = self.user_conf['api_key']
        if USER_SYS == "win":
            self.pypath = os.path.join(APP_PATH, "env", "python")
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
            user_chown(USER_CONF_PATH)
            return _template_user_conf
        with open( USER_CONF_PATH ) as f_user:
            return yaml.load(f_user, Loader=SafeLoader)
    
    def set_user_config(self, configs):
        with open( USER_CONF_PATH, "w" ) as f_user:
            yaml.dump(configs,f_user,sort_keys=False)
    
    #   > Return latest_services.config.yaml(write if not ignore_update)
    def get_services_config(self, ignore_update=False) -> (dict, dict):
        _req_res = None
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
        if ignore_update or ( isinstance(_req_res, requests.Response) and _req_res.status_code != 200 ):
            if not (os.path.isfile(SERV_CONF_PATH) or os.path.isfile(LAST_SERV_CONF_PATH)):
                print(f" [SERV_CONF] Not found-> {SERV_CONF_PATH}")
                print(f" [LAST_SERV_CONF] Not found-> {LAST_SERV_CONF_PATH}")
                raise EnvironmentError()
            else:
                with open( SERV_CONF_PATH ) as f_curr:
                    with open(LAST_SERV_CONF_PATH) as f_last:
                        return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)
        if _req_res.status_code == 200:
            # Create Latest Services Config File
            with open(LAST_SERV_CONF_PATH, "w") as fw:
                fw.write(_req_res.text)
            user_chown(LAST_SERV_CONF_PATH)

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
            user_chown(SERV_CONF_PATH)

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
            while True:
                try:
                    user_conf = self.get_user_config()
                    user_models = user_conf["models"]
                    break
                except:
                    pass
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
                "file": {
                    "file_name": ,
                    "file_url":
                },
                "image": {
                    "file_name": ,
                    "file_url":
                },
                "audio": {
                    "file_name": ,
                    "file_url":
                },
                "video": {
                    "file_name": ,
                    "file_url":
                },
                "text_prompt": "What is the content of this file? "
                **aditional iputs .. test and see
            },       
            "dep_args":{            # DEPENDENCIES VARS
                [dep_id_0]:{
                    "file": {
                        "file_name": ,
                        "file_url":
                    },
                    "image": {
                        "file_name": ,
                        "file_url":
                    },
                    "audio": {
                        "file_name": ,
                        "file_url":
                    },
                    "video": {
                        "file_name": ,
                        "file_url":
                    },
                    "text_prompt": "What is the content of this file? "
                    **aditional iputs .. test and see
                }
                [dep_id_1]:{
                    "file": {
                        "file_name": ,
                        "file_url":
                    },
                    "image": {
                        "file_name": ,
                        "file_url":
                    },
                    "audio": {
                        "file_name": ,
                        "file_url":
                    },
                    "video": {
                        "file_name": ,
                        "file_url":
                    },
                    "text_prompt": "What is the content of this file? "
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
            
            task = simple_post(API_URL, data=data, timeout=30)

            cprint(f"\nSignal DeSOTA that Model is wake up:\n{json.dumps(data, indent=2)}\nResponse Status = {task.status_code}", debug)
            if task.status_code != 200:
                continue

            '''
            Send a POST request to select a task
                Return: `select_task`
            ''' 
            data = {
                "api_key":self.user_api_key,
                "model":model,
                "select_task":I
            }
            
            select_task = simple_post(API_URL, data=data, timeout=30)

            cprint(f"Task Selection Request Payload:\n{json.dumps(data, indent=2)}\nResponse Status = {select_task.status_code}", debug)
            if select_task.status_code != 200:
                continue
            else:
                cprint(f"MODEL: {model}", debug)     
                
                cont = str(select_task.content.decode('UTF-8'))
                # print(cont)
                try:
                    # print(selected_task)
                    selected_task = json.loads(cont)
                    # print(json.dumps(selected_task, indent=2))
                except:
                    cprint(f"[ INFO ] -> API MODEL REQUEST FORMAT NOT JSON!\nResponse: {cont}", debug)   
                    cont = cont.replace("FIXME!!!", "")
                    ''' 
                    cont = cont.replace("\n", "")
                    #cont = cont.replace(r'\\\\', "")
                    #cont = cont.replace("\\\\\\", "")
                    #cont = cont.replace('\\', '')
                    #cont = cont.replace("\n", "")
                    #cont = cont.replace("\\", "")
                    '''
                    
                    try:
                        selected_task = json.loads(cont)
                    except:
                        selected_task = "error"
                        # print(selected_task)

                if "error" in selected_task:
                    #error = selected_task['error']
                    cprint(f"[ WARNING ] -> API Model Request fail for model `{model}`", debug)
                    selected_task = False
                    continue
                
                # cprint(selected_task, debug)     
                #cprint(selected_task['task'], debug)
                
                try:
                    task_dic = ast.literal_eval(str(selected_task['task']))
                except:
                    task_dic = None

                if isinstance(task_dic, dict) and task_dic:
                    model_request_dict['input_args'] = {}
                    for file_type, file_value in task_dic.items():
                        file_value_fixed = fix_file_name(file_value)
                        #print(file_type)
                        if file_type == "text":
                            # cprint(f'text select on 0', debug)   
                            model_request_dict['input_args']['text_prompt'] = download_file(file_value_fixed, get_file_content=True)
                        elif file_type in ['image', 'video', 'audio', 'file']:
                            model_request_dict['input_args'][file_type] = {}
                            model_request_dict['input_args'][file_type]['file_name'] = str(file_value_fixed)
                            model_request_dict['input_args'][file_type]['file_url'] = f"{API_UP}/{file_value_fixed}"
                        else:
                            model_request_dict['input_args'][file_type] = download_file(file_value_fixed)
                            
                    cprint(f"Request INPUT Files: {json.dumps(model_request_dict['input_args'], indent=2)}", debug)
                        
                    model_request_dict["task_type"] = selected_task['type']
                    task_dep = str(selected_task['dep']).replace("\\\\n", "").replace("\\", "")
                    task_dep = ast.literal_eval(task_dep)
                    model_request_dict["task_dep"] = task_dep
                    cprint(f"task type is {model_request_dict['task_type']}", debug)     
                    # cprint(f"task deps are {task_dep} {type(task_dep[0])}", debug)   
                    cprint(f"task deps are {task_dep}", debug)   
                    #if json.loads(str(task_dep.decode('UTF-8'))):
                    if task_dep != [-1]:
                        cprint("Dependencies:", debug)   
                        #deps = json.loads(str(task_dep.decode('UTF-8')))
                        model_request_dict['dep_args'] = {}
                        for dep_key, dep_args in task_dep.items():
                            try:
                                dep_id = int(dep_key)
                                dep_dic = json.loads(str(dep_args))
                            except:
                                try:
                                    dep_dic = find_json(str(dep_args))
                                    dep_dic = json.loads(dep_dic)   
                                except:
                                    dep_dic = None
                                    if not model_request_dict['dep_args'] and debug:
                                        cprint("no filename found" , debug)
                            if dep_dic:
                                model_request_dict['dep_args'][dep_id] = {}
                                for file_type, file_value in dep_dic.items():
                                    file_value_fixed = fix_file_name(file_value)
                                    #print(file_type)
                                    if file_type == "text":
                                        # cprint(f'text select on 0', debug)   
                                        model_request_dict['dep_args'][dep_id]['text_prompt'] = download_file(file_value_fixed, get_file_content=True)
                                    elif file_type in ['image', 'video', 'audio', 'file']:
                                        model_request_dict['dep_args'][dep_id][file_type] = {}
                                        model_request_dict['dep_args'][dep_id][file_type]['file_name'] = str(file_value_fixed)
                                        model_request_dict['dep_args'][dep_id][file_type]['file_url'] = f"{API_UP}/{file_value_fixed}"
                                    else:
                                        model_request_dict['dep_args'][dep_id][file_type] = download_file(file_value_fixed)
                                            
                        cprint(f"Request DEP Files: {json.dumps(model_request_dict['dep_args'], indent=2)}", debug)
                        

                    cprint("No Dependencies!", debug)    
                    #exit()

                cprint(f"No task for {model}!", debug)   
                #exit()


            model_request_dict["task_model"] = model    # Return Model to work on

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

        # TODO: Sorry Kris :')
        # if model_request_dict["task_type"] in ["image-to-image", "seg-image-to-image", "canny-image-to-image", "softedge-image-to-image", "lines-image-to-image", "normals-image-to-image", "pose-image-to-image"]:
        #     for file_type, file_value in model_request_dict['input_args']:
        #         if (not model_request_dict['files'].endswith('.jpg')) and (not model_request_dict['files'].endswith('.png')) and (not model_request_dict['files'].endswith('.png')) and (not model_request_dict['files'].endswith('.gif')) and (not model_request_dict['files'].endswith('.bmp')):
        #             model_request_dict['text_prompt'] = model_request_dict['files']
        #             model_request_dict["task_type"] = model_request_dict["task_type"].replace("image-to-", "text-to-")
        
        return model_request_dict


    # Handle Model Service
    #   > Start Service
    def start_model_serv(self, model_id) -> None:
        _model_params = self.serv_conf["services_params"][model_id]

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
            user_chown(LAST_UP_EPOCH)
            return "go for it"
        
        cprint(f"[ TIMER DEBUG ] - MEMORY EXIST", DEBUG)
        with open(LAST_UP_EPOCH, "r") as fr:
            _last_up_ep = fr.read()
        _last_up_ep = float(_last_up_ep)
        user_chown(LAST_UP_EPOCH)
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
        if DERRUNER_ID not in model_ids:
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
        user_chown(target_path)
        return target_path

    #   > Request Model(s) reinstalation
    def request_model_reinstall(self, reinstall_models, init=False) -> bool:
        '''
        Exit Codes:
         1 - Reinstall Started W/O DeRunner (Not Required to Stop Services)
         2 - Reinstall Started W DeRunner
         9 - Reinstall Fail
        10 - Submodel Critical Fail
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
        
        if submodel_critical_fail:
            _res_uconf = _compare_conf.copy()
            try:
                # edit user config admissions
                if "admissions" in _compare_conf and _compare_conf["admissions"]:
                    for _model in reinstall_models:
                        for admn_key, admissions in _compare_conf["admissions"].items():
                            if _model in admissions:
                                _res_uconf["admissions"][admn_key].pop(_model)
            except:
                pass
            cprint(f"[ UPGRADE ] -> pre user_configs: {json.dumps(_res_uconf, indent = 2)}", DEBUG)
            self.set_user_config(_res_uconf)
            return 10

        cprint(f"[ UPGRADE ] -> pre user_configs: {json.dumps(_res_uconf, indent = 2)}", DEBUG)
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
        cprint(f"[ UPGRADE ] -> pre services_configs: {json.dumps(_res_sconf, indent = 2)}", DEBUG)
        delogger(f"[ UPGRADE ] -> pre services_configs: {json.dumps(_res_sconf)}")
        _compare_conf = _res_sconf.copy()
        for _model in rm_models:
            if _model in _compare_conf["services_params"]:
                _res_sconf["services_params"].pop(_model)
        cprint(f"[ UPGRADE ] -> pos services_configs: {json.dumps(_res_sconf, indent = 2)}", DEBUG)
        delogger(f"[ UPGRADE ] -> pos services_configs: {json.dumps(_res_sconf)}")
        self.set_services_config(_res_sconf)
        if DEVELOPMENT:
            return "devop"
        
        # Force DeRunner Restart
        if DERRUNER_ID not in model_ids:
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
        user_chown(target_path)
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
        0 - No Model to Upgrade
        1 - Upgrade Started W/O DeRunner (Not Required to Stop Services)
        2 - Upgrade Started W DeRunner
        9 - Upgrade Fail
        '''
        # Timer check
        upgrade_timer = self.handle_upgrade_timer()
        if upgrade_timer != "go for it":
            return 0
        

        delogger(f"[ INFO:{int(time.time())} ] - Searching for models upgrade.")
        print(f"[ INFO:{int(time.time())} ] - Searching for models upgrade.")
        # UPGRADE CONFIGURATIONS (Target: self.last_serv_conf)
        self.__init__()
        user_models = self.user_conf["models"]
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
        if DEBUG or USER_SYS == "lin":
            cprint(f'Quiet Subprocess Requested:\n\t{" ".join(cmd_list)}', DEBUG)
            _sproc = Popen(
                cmd_list
            )
        elif USER_SYS == "win":
            _sproc = Popen(
                cmd_list,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
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
    
    def grab_model_info(self, model, version):
        # TODO: Implement DeSota Model Info Req
        #   perhaps is only required test "res url upload" and "model timeout"
        match model:
            case "franciscomvargas/deurlcruncher":
                return {
                    "cmd": [
                        '--model', model,
                        '--input-query', 'Search',        # Can go to service_config
                        '--input-type', 'text',             # Can go to service_config
                        '--input-file', '"Search Engine"',  # Can go to service_config
                        # report-file > URL OF DESOTA IN THE FUTURE
                        '--report-file', os.path.join(DESOTA_ROOT_PATH, "duc_report.json")
                    ],
                    "timeout": 180  # Can go to service_config ( NOT EDITABLE AFTER)
                }
            case "franciscomvargas/whisper.cpp":
                return {
                    "cmd": [
                        '--model', model,
                        '--input-query', 'Transcribe',  # Can go to service_config
                        '--input-type', 'audio',        # Can go to service_config
                        '--input-file', 'Desota/Desota_Models/WhisperCpp/samples/jfk.wav',  # Can go to service_config
                        # report-file > URL OF DESOTA IN THE FUTURE
                        '--report-file', os.path.join(DESOTA_ROOT_PATH, "whisper_report.json")
                    ],
                    "timeout": 240  # Can go to service_config ( NOT EDITABLE AFTER)
                }
            case "franciscomvargas/descraper/url":
                return {
                    "cmd": [
                        '--model', model,
                        '--input-query', '"Search"',        # Can go to service_config
                        '--input-dict', '{"url":"https://pt.wikipedia.org/wiki/Os_Simpsons"}',   # Can go to service_config
                        # report-file > URL OF DESOTA IN THE FUTURE
                        '--report-file', os.path.join(DESOTA_ROOT_PATH, "descraper_url_report.json")
                    ],
                    "timeout": 60   # Can go to service_config ( NOT EDITABLE AFTER)
                }
            case "franciscomvargas/descraper/html":
                return {
                    "cmd": [
                        '--model', model,
                        '--input-query', '"Search"',        # Can go to service_config
                        '--input-dict', '{"url":"https://pt.wikipedia.org/wiki/Os_Simpsons"}',   # Can go to service_config
                        # report-file > URL OF DESOTA IN THE FUTURE
                        '--report-file', os.path.join(DESOTA_ROOT_PATH, "descraper_html_report.json")
                    ],
                    "timeout": 60   # Can go to service_config ( NOT EDITABLE AFTER)
                }
            case _:
                print(f"[ RUNNER TESTER ] -> Error: Model [{model}] info not found. Derunner>get_model_info()")
                delogger(f"[ RUNNER TESTER ] -> Error: Model [{model}] info not found. Derunner>get_model_info()")
                return None
        
    def grab_models2test(self):
        # Grab Function required Configs
        user_config = self.get_user_config()
        mem_user_config = self.get_user_config()
        user_models = self.grab_runner_models()
        user_key = user_config["api_key"]
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
                            # TODO: DeSOTA API ADD MODEL to this API
                        self.set_user_config(user_config)
            # Final Own API Admission Confirmation
            if model in user_config["admissions"][user_key] and user_config["admissions"][user_key][model] == version:
                models_tested.append(model)
                continue
            else:
                models2test[model] = version
        return models2test, models_tested
    
    def test_models(self):
        # Monitor newby models to test
        models2test, models_tested = self.grab_models2test()
        # If no Model Found
        if not models2test:
            return models_tested

        # Test Models Logic Bellow
        test_script_path = os.path.join(APP_PATH, "Tools", "builtin_model_tester.py")
        for model, version in models2test.items():
            # INFO
            print(f"[ INFO ] -> Model Tester start:\n  Model ID: {model}")
            delogger(f"[ INFO ] -> Model Tester start:\n  Model ID: {model}")
            
            # Get Model Test CMD
            # TODO: expert info will be provided by desota
            model_test_info = self.grab_model_info(model, version)
            # Confirm Info
            if not model_test_info:
                continue
            else:
                for key in ["cmd", "timeout"]:
                    if key not in model_test_info or not model_test_info[key]:
                        continue
            model_test_cmd = model_test_info["cmd"]
            model_test_timeout = model_test_info["timeout"]
            model_test_cmd = [self.pypath, test_script_path] + model_test_cmd
            print("TEST CMD:", " ".join(model_test_cmd))
            test_res = self.quiet_subprocess(model_test_cmd, model_test_timeout)
            if test_res == 0:
                self.__init__(ignore_update=True)
                user_conf = self.user_conf
                user_conf["admissions"][self.user_api_key].update({model:version})
                self.set_user_config(user_conf)
                models_tested.append(model)
                print(f"[ INFO ] -> Model Tester end:\n  Model ID: {model}\n  Result: SUCESS")
                delogger(f"[ INFO ] -> Model Tester end:\n  Model ID: {model}\n  Result: SUCESS")
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
            else:
                # REQUEST MODEL UNINSTALL
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
        last_signal_time = start_time
        # Create tmp model_req.yaml with request params for model runner
        _tmp_req_path = os.path.join(TMP_PATH, f"tmp_model_req{int(time.time())}.yaml")
        with open(_tmp_req_path, 'w',) as fw:
            yaml.dump(model_req,fw,sort_keys=False)

        # Model Vars
        _model_id = model_req['task_model']                                             # Model Name
        _model_runner_param = self.serv_conf["services_params"][_model_id]  # Model params from services.config.yaml
        _model_runner_sys_param = _model_runner_param[USER_SYS] 
        _model_runner = os.path.join(USER_PATH, _model_runner_sys_param["project_dir"], _model_runner_sys_param["desota_runner"])          # Model runner path
        _model_runner_py = os.path.join(USER_PATH, _model_runner_sys_param["python_path"])    # Python with model runner packages

        # API Response URL
        _model_res_url = f"{API_URL}?api_key={self.user_api_key}&model={model_req['task_model']}&send_task=" + model_req['task_id']
        
        # Start / Wait Model
        # retrieved from https://stackoverflow.com/a/62226026
        if DEBUG or USER_SYS == "lin":
            cprint(f'Model runner cmd:\n\t{" ".join([_model_runner_py, _model_runner, "--model_req", _tmp_req_path, "--model_res_url", _model_res_url])}', DEBUG)
            _sproc = Popen(
                [
                    _model_runner_py, _model_runner, 
                    "--model_req", _tmp_req_path, 
                    "--model_res_url", _model_res_url
                ]
            )
        elif USER_SYS == "win":
            _sproc = Popen(
                [
                    _model_runner_py, _model_runner, 
                    "--model_req", _tmp_req_path, 
                    "--model_res_url", _model_res_url
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            return
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

                # Check for untested models
                admmit_models = self.test_models()
                
                model_req = self.monitor_model_request(admmit_models, debug=DEBUG)

                if not model_req:
                    continue
                print("*"*80)
                delogger("*"*80)
                print(f"[ INFO ] -> Incoming Model Request:\n{json.dumps(model_req, indent=2)}")
                delogger(f"[ INFO ] -> Incoming Model Request:\n{json.dumps(model_req, indent=2)}")

                self.start_model_serv(model_req['task_model'])
                
                model_res = self.call_model(model_req)

                # TODO : Handle process return code
                error_level = None
                if model_res == 1:
                    print(f"[ TODO ] -> Model INPUT ERROR (Write exec_state = 9)")
                    error_level = 9
                    error_msg = "Model INPUT ERROR"
                elif model_res == 2:
                    print(f"[ TODO ] -> Model OUTPUT ERROR (Retry in another server)")
                    error_level = 8
                    error_msg = "Model OUTPUT ERROR"
                elif model_res == 3:
                    print(f"[ TODO ] -> Write Result to DeSOTA ERROR (Retry in another server)")
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
                if not DEVELOPMENT:
                    _reinstall_model = DERRUNER_ID
                pass

            if error_level:
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
                req_reinstall = self.request_model_reinstall(_reinstall_model, init=True)
                # DeRunner Upgrade Requested
                if req_reinstall == 2:
                    # STOP SERVICE
                    exit(66)

if __name__ == "__main__":
    check_status()
    derunner_class = Derunner()
    derunner_class.mainloop()
