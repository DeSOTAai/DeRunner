import time
import requests
import subprocess
from subprocess import check_output
from subprocess import check_call, call, CalledProcessError
from subprocess import Popen, CREATE_NEW_CONSOLE
import ast
import json
import io
import os
import re
import shutil
# import pyyaml module
import yaml
from yaml.loader import SafeLoader
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-hs', '--handshake',
                    help='Service Status Request',
                    action='store_true')

I=0
DEBUG = False

# :: os.getcwd() = C:\users\[user]\Desota\DeRunner
# WORKING_FOLDER = os.getcwd()
WORKING_FOLDER = os.path.dirname(os.path.realpath(__file__))

USER_PATH = "\\".join(WORKING_FOLDER.split("\\")[:-2])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")

APP_PATH = os.path.join(DESOTA_ROOT_PATH, "DeRunner")
MANAGER_TOOLS_PATH = os.path.join(DESOTA_ROOT_PATH, "DeManagerTools")
CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")

USER_CONF_PATH = os.path.join(CONFIG_PATH, "user.config.yaml")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")
LAST_SERV_CONF_PATH = os.path.join(CONFIG_PATH, "latest_services_config.yaml")
SERVICE_TOOLS_PATH = os.path.join(CONFIG_PATH, "Services")
LAST_UP_EPOCH = os.path.join(SERVICE_TOOLS_PATH, "last_upgrade_epoch.txt")

#!!!! Upgrade Frequency in secs
UPG_FREQ = 86400    # 24h
# UPG_FREQ = 10     # DEBUG

# Services Configurations - Latest version URL
LATEST_SERV_CONF_RAW = "https://raw.githubusercontent.com/DeSOTAai/DeRunner/main/Assets/latest_services.config.yaml"

API_URL = "https://desota.net/assistant/api.php"
API_UP =  "https://desota.net/assistant/api_uploads"

# DeSOTA Services that don't run with DeRunner
IGNORE_MODELS = ["desotaai/derunner"] 

# MODEL_TO_METHOD = configs['model_to_method']

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
    if condition:
        print(query)
#   > Log to service.log
def delogger(query):
    _log_path = os.path.join(WORKING_FOLDER, "service.log")
    if not os.path.isfile(_log_path):
        with open(_log_path, "w") as fw:
            fw.write(f"File Forced Creation by DeRunner\n")

    with open(_log_path, "a") as fa:
        if isinstance(query, str) or isinstance(query, int) or isinstance(query, float):
            fa.write(f"{query}\n")
        elif isinstance(query, list):
            fa.writelines(query)
        elif isinstance(query, dict):
            fa.write(json.dumps(query, indent=2), "\n")
            fa.write("\n")


# DeRunner Class
class Derunner():
    # Configurations
    def __init__(self) -> None:
        self.serv_conf, self.last_serv_conf = self.get_services_config()
        self.user_conf = self.get_user_config()
        self.user_system = self.user_conf["system"]
        self.user_models = self.user_conf['models']
        self.user_api_key = self.user_conf['api_key']

    #   > Grab User Configurations
    def get_user_config(self) -> dict:
        if not os.path.isfile(USER_CONF_PATH):
            print(f" [USER_CONF] Not found-> {USER_CONF_PATH}")
            raise EnvironmentError()
        with open( USER_CONF_PATH ) as f_user:
            return yaml.load(f_user, Loader=SafeLoader)
    
    #   > Return latest_services.config.yaml(write if not ignore_update)
    def get_services_config(self, ignore_update=False) -> (dict, dict):
        if ignore_update:
            if not (os.path.isfile(SERV_CONF_PATH) or os.path.isfile(LAST_SERV_CONF_PATH)):
                print(f" [SERV_CONF] Not found-> {SERV_CONF_PATH}")
                print(f" [LAST_SERV_CONF] Not found-> {LAST_SERV_CONF_PATH}")
                raise EnvironmentError()
            with open( SERV_CONF_PATH ) as f_curr:
                with open(LAST_SERV_CONF_PATH) as f_last:
                    return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)
        _req_res = requests.get(LATEST_SERV_CONF_RAW)
        if _req_res.status_code != 200:
            print(f" [SERV_CONF] Not found-> {SERV_CONF_PATH}")
            print(f" [LAST_SERV_CONF] Not found-> {LAST_SERV_CONF_PATH}")
            raise EnvironmentError()
        else:
            # Create Latest Services Config File
            with open(LAST_SERV_CONF_PATH, "w") as fw:
                fw.write(_req_res.text)

            # Create Services Config File if don't exist
            if not os.path.isfile(SERV_CONF_PATH):
                with open(LAST_SERV_CONF_PATH, "w") as fw:
                    fw.write(_req_res.text)

            with open( SERV_CONF_PATH ) as f_curr:
                with open(LAST_SERV_CONF_PATH) as f_last:
                    return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)


    # DeSOTA API Monitor
    #   > Get child models and remove desota tools (IGNORE_MODELS)
    def grab_all_user_models(self, ignore_models=IGNORE_MODELS) -> list:
        all_user_models = []
        
        for model in list(self.user_models.keys()):
            if model in ignore_models:
                continue
            
            all_user_models.append(model)
            _model_params = self.serv_conf["services_params"][model]
            # print(f" [ DEBUG ALL USER MODELS ] - {model} params = {json.dumps(_model_params, indent=2)}")

            _child_models = None if "child_models" not in _model_params and not _model_params["child_models"] else _model_params["child_models"]
            # print(f" [ DEBUG ALL USER MODELS ] - {model} child models = {_child_models}")
            if _child_models:
                if isinstance(_child_models, str):
                    _child_models = [_child_models]
                if isinstance(_child_models, list):
                    for _child_model in _child_models:
                        if _child_model in self.serv_conf["services_params"] and _child_model not in all_user_models:
                            all_user_models.append(_child_model)
        return all_user_models
    
    #   > Check for model request
    def monitor_model_request(self, ignore_models=IGNORE_MODELS, debug=False) -> dict:
        global I
        I += 1
        
        cprint(f"Running...{I}", debug) # Conditional Print

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
        
        # Grab Models + Child Models (services.config.yaml)
        _all_user_models = self.grab_all_user_models(ignore_models)
        cprint(f"[ INFO ] -> All User Models: {json.dumps(_all_user_models, indent=4)}", debug)

        if not _all_user_models:
            return None
        
        for model in _all_user_models:
            '''
            Send a POST request to API to get a task
                Return: `task`
            ''' 

            data = {
                "api_key":self.user_api_key,
                "model":model
            }
            task = requests.post(API_URL, data=data, timeout=30)
            # print(f"Task Request Payload:\n{json.dumps(data, indent=2)}\nResponse Status = {task.status_code}")
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
            select_task = requests.post(API_URL, data=data)
            # print(f"Task Selection Request Payload:\n{json.dumps(data, indent=2)}\nResponse Status = {select_task.status_code}")
            if select_task.status_code != 200:
                continue
            else:
                cprint(f"MODEL: {model}", debug)     # Conditional Print
                
                cont = str(select_task.content.decode('UTF-8'))
                # print(cont)
                try:
                    # print(selected_task)
                    selected_task = json.loads(cont)
                except:
                    cprint(f"[ INFO ] -> API MODEL REQUEST FORMAT NOT JSON!\nResponse: {cont}", debug)   # Conditional Print
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
                        print(selected_task)

                if "error" in selected_task:
                    #error = selected_task['error']
                    # print(f"[ WARNING ] -> API Model Request fail for model `{model}`")
                    selected_task = False
                    continue
                
                cprint(selected_task, debug)     # Conditional Print
                #cprint(selected_task['task'], debug)
                
                try:
                    task_dic = ast.literal_eval(str(selected_task['task']))
                except:
                    task_dic = None

                if isinstance(task_dic, dict) and task_dic:
                    model_request_dict['input_args'] = {}
                    for file_type, file_value in task_dic.items():
                        #print(file_type)
                        if file_type == "text":
                            # cprint(f'text select on 0', debug)   # Conditional Print
                            model_request_dict['input_args']['text_prompt'] = str(file_value)
                        elif file_type in ['image', 'video', 'audio', 'file']:
                            model_request_dict['input_args'][file_type] = {}
                            model_request_dict['input_args'][file_type]['file_name'] = str(file_value)
                            model_request_dict['input_args'][file_type]['file_url'] = f"{API_UP}/{file_value}"
                        else:
                            model_request_dict['input_args'][file_type] = str(file_value)
                            
                    cprint(f"Request INPUT Files: {json.dumps(model_request_dict['input_args'], indent=2)}", debug)
                        
                    model_request_dict["task_type"] = selected_task['type']
                    task_dep = str(selected_task['dep']).replace("\\\\n", "").replace("\\", "")
                    task_dep = ast.literal_eval(task_dep)
                    model_request_dict["task_dep"] = task_dep
                    cprint(f"task type is {model_request_dict['task_type']}", debug)     # Conditional Print
                    # cprint(f"task deps are {task_dep} {type(task_dep[0])}", debug)   # Conditional Print
                    cprint(f"task deps are {task_dep}", debug)   # Conditional Print
                    #if json.loads(str(task_dep.decode('UTF-8'))):
                    if task_dep != [-1]:
                        cprint("Dependencies:", debug)   # Conditional Print
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
                                        print("no filename found")
                            if dep_dic:
                                model_request_dict['dep_args'][dep_id] = {}
                                for file_type, file_value in dep_dic.items():
                                    #print(file_type)
                                    if file_type == "text":
                                        # cprint(f'text select on 0', debug)   # Conditional Print
                                        model_request_dict['dep_args'][dep_id]['text_prompt'] = str(file_value)
                                    elif file_type in ['image', 'video', 'audio', 'file']:
                                        model_request_dict['dep_args'][dep_id][file_type] = {}
                                        model_request_dict['dep_args'][dep_id][file_type]['file_name'] = str(file_value)
                                        model_request_dict['dep_args'][dep_id][file_type]['file_url'] = f"{API_UP}/{file_value}"
                                    else:
                                        model_request_dict['dep_args'][dep_id][file_type] = str(file_value)
                                            
                        cprint(f"Request DEP Files: {json.dumps(model_request_dict['dep_args'], indent=2)}", debug)
                        

                    cprint("No Dependencies!", debug)    # Conditional Print
                    #exit()

                cprint(f"No task for {model}!", debug)   # Conditional Print
                #exit()


            model_request_dict["task_model"] = model    # Return Model to work on

            if selected_task and "error" not in selected_task:
                break
        
        if not selected_task:
            cprint("Byeeee\n", debug)    # Conditional Print
            return None

        model_request_dict["task_args"] = task_dic
        model_request_dict['task_id'] = selected_task['id']

        #send_task_data = {
        #    "api_key":self.user_api_key,
        #    "model":model
        #}
        #sendTask = requests.post(API_URL, data=data)

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
            _model_serv = self.serv_conf["services_params"][model_id][self.user_system]
        else:
            _model_serv = self.serv_conf["services_params"][ _model_params["parent_model"] ][self.user_system]

        _model_starter = os.path.join(USER_PATH, _model_serv["service_path"], _model_serv["starter"]) if _model_serv["starter"] else None
        if not _model_starter:
            return
        
        if DEBUG:
            print(f'Model start cmd:\n\t{_model_starter}')
            _sproc = Popen(
                [_model_starter]
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
        
        _model_serv = _model_params[self.user_system]

        _model_stoper = os.path.join(USER_PATH, _model_serv["service_path"], _model_serv["stoper"]) if _model_serv["stoper"] else None
        if not _model_stoper:
            return None
        
        if DEBUG:
            print(f'Model stop cmd:\n\t{_model_stoper}')
            _sproc = Popen(
                [_model_stoper]
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
            return "go for it"
        
        cprint(f"[ TIMER DEBUG ] - MEMORY EXIST", False)
        with open(LAST_UP_EPOCH, "r") as fr:
            _last_up_ep = fr.read()
        _last_up_ep = float(_last_up_ep)

        if time.time() - _last_up_ep >= UPG_FREQ:
            cprint(f"[ TIMER DEBUG ] - SECS PASSED SINCE LAST UPG = {int(time.time() - _last_up_ep)}", False)
            return "go for it"
        return None

    #   > Create Model(s) installer for reinstalation
    def create_model_reinstalation(self, model_ids) -> str:
        if self.user_system == "win":
            # 1 - CRAWL CONFS
            target_path = os.path.join(DESOTA_ROOT_PATH, f"tmp_model_install{int(time.time())}.bat")
            
            # 2 - BAT HEADER
            _tmp_file_lines = ["@ECHO OFF\n"]
            _tmp_file_lines += [
                "net session >NUL 2>NUL\n",
                "IF %errorLevel% NEQ 0 (\n",
                "\tgoto UACPrompt\n",
                ") ELSE (\n",
                "\tgoto gotAdmin\n",
                ")\n",
                ":UACPrompt\n",
                'powershell -Command "Start-Process -Wait -Verb RunAs -FilePath \'%0\' -ArgumentList \'am_admin\'" \n',
                "exit /B\n",
                ":gotAdmin\n",
                'pushd "%CD%"\n',
                f'CD /D "{DESOTA_ROOT_PATH}"\n'
            ]
            
            # 2.1 - Wait DeRunner Service STOP
            derunner_status_path = os.path.join(APP_PATH, "executables", "Windows", "derunner.status.bat")
            derunner_status_res = os.path.join(APP_PATH, "derunner_status.txt")
            _tmp_file_lines += [
                ":wait_derunner_stop\n",
                f"start /B /WAIT {derunner_status_path} {derunner_status_res}\n",
                f"set /p derunner_status=<{derunner_status_res}\n",
                "IF %derunner_status% NEQ SERVICE_STOPPED (\n",
                "\tgoto wait_derunner_stop\n",
                ") ELSE (\n",
                f"\tdel {derunner_status_res}\n",
                ")\n",
            ]

            # 3 - Stop All Services
            _gen_serv_stoper = os.path.join(SERVICE_TOOLS_PATH, "models_stopper.bat")
            if os.path.isfile(_gen_serv_stoper):
                _tmp_file_lines.append(f"start /B /WAIT {_gen_serv_stoper}\n")

            if isinstance(model_ids, str):
                model_ids = [model_ids]
            
            if isinstance(model_ids, list):
                for _model in model_ids:
                    # 4.1 - Append Model Installer
                    _model_params = self.last_serv_conf['services_params'][_model][self.user_system]
                    _installer_url = _model_params['installer']
                    _installer_args = _model_params['installer_args'] if 'installer_args' in _model_params and _model_params['installer_args'] else []
                    _installer_args += ["/fromrunner"]
                    _model_version = _model_params['version']
                    _installer_name = _installer_url.split('/')[-1]
                    _tmp_install_path = os.path.join(USER_PATH, _installer_name)
                    
                    _tmp_file_lines.append(f'powershell -command "Invoke-WebRequest -Uri {_installer_url} -OutFile {_tmp_install_path}"\n')
                    _tmp_file_lines.append(f'start /B /WAIT {_tmp_install_path} {" ".join(_installer_args)}\n')
                    _tmp_file_lines.append(f'del {_tmp_install_path}\n')
                    
                    # 4.2 - Update user models
                    _new_model = json.dumps({
                        _model: _model_version
                    }).replace(" ", "").replace('"', '\\"')
                    
                    _tmp_file_lines.append(f'call {MANAGER_TOOLS_PATH}\env\python {MANAGER_TOOLS_PATH}\Tools\SetUserConfigs.py --key models --value "{_new_model}"  > NUL 2>NUL\n')
        
            ## after instalation!!
            #   > Update Services Config with params from Latest Services Config
            #   > Update Models Starter for Run constantly models
            #   > Update Models Stoper
            _tmp_file_lines.append(f'call {APP_PATH}\env\python {APP_PATH}\Tools\\after_model_reinstall.py > NUL 2>NUL\n')

            # 5 - Create Start Run Constantly Services
            _gen_serv_starter = os.path.join(SERVICE_TOOLS_PATH, "models_starter.bat")
            _tmp_file_lines.append(f"IF EXIST {_gen_serv_starter} start /B /WAIT {_gen_serv_starter}\n")
            
            # 5 - Delete Bat at end of instalation - retrieved from https://stackoverflow.com/a/20333152
            _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n')
            #_tmp_file_lines.append("PAUSE\n") # DEBUG

            # 6 - Create Installer Bat
            with open(target_path, "w") as fw:
                fw.writelines(_tmp_file_lines)
                
            return target_path

    #   > Request Model(s) reinstalation
    def request_model_reinstall(self, _reinstall_model, init=False) -> int:
        if init:
            # UPGRADE CONFIGURATIONS (Target: self.last_serv_conf)
            self.__init__()

        _reinstall_path = self.create_model_reinstalation(_reinstall_model)
        _reinstall_cmd = [_reinstall_path]
        print(f" [ WARNING ] -> Model Reinstalation required:\n\tmodel: {_reinstall_model}\n\treinstall cmd: {' '.join(_reinstall_cmd)}")

        # os.spawnl(os.P_OVERLAY, str(_reinstall_path), )
        if self.user_system == "win":
            # retrieved from https://stackoverflow.com/a/14797454
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008
            Popen(
                _reinstall_cmd,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            )
        return 0
    
    #   > Check for upgrades
    def req_service_upgrade(self) -> int:
        # Timer check
        upgrade_timer = self.handle_upgrade_timer()
        if upgrade_timer != "go for it":
            return None
        

        print(f"[ INFO:{int(time.time())} ] - Searching for models upgrade.")
        # UPGRADE CONFIGURATIONS (Target: self.last_serv_conf)
        self.__init__()
        
        _upg_models = []
        for _model in list(self.user_models.keys()):
            curr_version = self.serv_conf["services_params"][_model][self.user_system]["version"]
            last_version = self.last_serv_conf["services_params"][_model][self.user_system]["version"]
            if curr_version != last_version:
                _upg_models.append(_model)
        if not _upg_models:
            self.handle_upgrade_timer(create=True)
            return None
        
        print(f"[ INFO:{int(time.time())} ] - Founded the following models to upgrade: {_upg_models}")
        req_reinstall = self.request_model_reinstall(_upg_models)
        if req_reinstall == 0:
            self.handle_upgrade_timer(create=True)
            return 0


    # Call Model Runner
    def call_model(self, model_req) -> int:
        # Create tmp model_req.yaml with request params for model runner
        _tmp_req_path = os.path.join(APP_PATH, f"tmp_model_req{int(time.time())}.yaml")
        with open(_tmp_req_path, 'w',) as fw:
            yaml.dump(model_req,fw,sort_keys=False)

        # Model Vars
        _model_id = model_req['task_model']                                             # Model Name
        _model_runner_param = self.serv_conf["services_params"][_model_id][self.user_system]      # Model params from services.config.yaml
        _model_runner = os.path.join(USER_PATH, _model_runner_param["runner"])          # Model runner path
        _model_runner_py = os.path.join(USER_PATH, _model_runner_param["runner_py"])    # Python with model runner packages

        # API Response URL
        _model_res_url = f"{API_URL}?api_key={self.user_api_key}&model={model_req['task_model']}&send_task=" + model_req['task_id']
        
        # Start / Wait Model
        # retrieved from https://stackoverflow.com/a/62226026
        if DEBUG:
            print(f'Model runner cmd:\n\t{" ".join([_model_runner_py, _model_runner, "--model_req", _tmp_req_path, "--model_res_url", _model_res_url])}')
            _sproc = Popen(
                [
                    _model_runner_py, _model_runner, 
                    "--model_req", _tmp_req_path, 
                    "--model_res_url", _model_res_url
                ]
            )
        else:
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
        # TODO: implement model timeout
        while True:
            _ret_code = _sproc.poll()
            if _ret_code != None:
                break
            continue

        if os.path.isfile(_tmp_req_path):
            os.remove(_tmp_req_path)

        print(f"[ INFO ] -> Model `{model_req['task_model']}` returncode = {_ret_code}")
        delogger(f"[ INFO ] -> Model `{model_req['task_model']}` returncode = {_ret_code}")
        
        return _ret_code


    # Main DeRunner Loop
    def mainloop(self, args) -> None:
        # Handshake - Service checker
        if args.handshake:
            print('{"status":"ready"}')
            return 0
        
        # Print Configurations
        print("Runner Up!")
        delogger("Runner Up!")
        
        print(f"[ INFO ] -> Configurations:\n{json.dumps(self.user_conf, indent=2)}")
        delogger(f"[ INFO ] -> Configurations:\n{json.dumps(self.user_conf, indent=2)}")

        _ignore_models = IGNORE_MODELS.copy()
        _reinstall_model = None
        while True:
            try:
                # clear()
                # TODO : Test new installed models here...

                # Check for model upgrades
                req_serv_upg = self.req_service_upgrade()
                if req_serv_upg == 0:
                    # STOP SERVICE
                    exit(666)

                model_req = self.monitor_model_request(ignore_models=_ignore_models, debug=False)

                if model_req == None:
                    continue
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
            except ConnectionError as ce:
                print(f"[ WARNING ] -> DeRunner Lost Internet Acess: {ce}")
                error_level = 8
                error_msg = "ConnectionError"
                #TODO: implement
                pass
            except Exception as e:
                print(f"[ CRITICAL FAIL ] -> Re-Install DeRunner: {e}")
                delogger(f"[ CRITICAL FAIL ] -> Re-Install DeRunner: {e}")
                error_level = 8
                error_msg = f"DeRunner CRITICAL FAIL: {e}"
                _reinstall_model = "desotaai/derunner"
                pass
            
            if error_level:
                error_url = f"{API_URL}?api_key={self.user_api_key}&model={model_req['task_model']}&send_task={model_req['task_id']}&error={error_level}&error_msg={error_msg}" 
                error_res = requests.post(url = error_url)
                print(f"[ INFO ] -> DeSOTA ERROR Upload:\n\tURL: {error_url}\n\tRES: {json.dumps(error_res.json(), indent=2)}")
                delogger(f"[ INFO ] -> DeSOTA ERROR Upload:\n\tURL: {error_url}\n\tRES: {json.dumps(error_res.json(), indent=2)}")
                time.sleep(.8)

            
            if _reinstall_model:
                req_reinstall = self.request_model_reinstall(_reinstall_model, init=True)
                if req_reinstall == 0:
                    # STOP SERVICE
                    exit(666)

if __name__ == "__main__":
    args = parser.parse_args()
    derunner_class = Derunner()
    # derunner_class.debug(args)
    derunner_class.mainloop(args)
