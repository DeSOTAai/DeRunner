import sys, os, io, shutil, time
import json, ast, re

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
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-hs', '--handshake',
                    help='Service Status Request',
                    action='store_true')

I=0
DEBUG = False

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
WORKING_FOLDER = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = os.path.join(WORKING_FOLDER, "service.log")
def user_chown(path):
    '''Remove root previleges for files and folders: Required for Linux'''
    if USER_SYS == "lin":
        #CURR_PATH=/home/[USER]/Desota/DeRunner
        USER=str(WORKING_FOLDER).split("/")[-3]
        os.system(f"chown -R {USER} {path}")
    return


if USER_SYS == "win":
    USER_PATH = "\\".join(WORKING_FOLDER.split("\\")[:-2])
elif USER_SYS == "lin":
    USER_PATH = "/".join(WORKING_FOLDER.split("/")[:-2])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
LOG_PATH = os.path.join(DESOTA_ROOT_PATH, "demanager.log")

APP_PATH = os.path.join(DESOTA_ROOT_PATH, "DeRunner")
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
    '''Conditional print'''
    if condition:
        print(query)
#   > Log to service.log
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

# DeRunner Class
class Derunner():
    # Configurations
    def __init__(self, ignore_update=False) -> None:
        self.serv_conf, self.last_serv_conf = self.get_services_config(ignore_update=ignore_update)
        self.user_conf = self.get_user_config()
        self.user_models = self.user_conf['models']
        self.user_api_key = self.user_conf['api_key']

    #   > Grab User Configurations
    def get_user_config(self) -> dict:
        if not os.path.isfile(USER_CONF_PATH):
            _template_user_conf={
                "user_api": None,
                "models":None,
                "system": USER_SYS
            }
            with open(USER_CONF_PATH, 'w',) as fw:
                yaml.dump(_template_user_conf,fw,sort_keys=False)
            user_chown(USER_CONF_PATH)
            return _template_user_conf
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
        
        # Create Latest Services Config File
        with open(LAST_SERV_CONF_PATH, "w") as fw:
            fw.write(_req_res.text)

        # Create Services Config File if don't exist
        if not os.path.isfile(SERV_CONF_PATH):
            with open(LAST_SERV_CONF_PATH) as fls:
                _template_serv=yaml.load(fls, Loader=SafeLoader)
            _template_serv["services_params"] = {}
            with open(SERV_CONF_PATH, "w") as fw:
                yaml.dump(_template_serv,fw,sort_keys=False)        
            user_chown(SERV_CONF_PATH)
        user_chown(LAST_SERV_CONF_PATH)

        with open( SERV_CONF_PATH ) as f_curr:
            with open(LAST_SERV_CONF_PATH) as f_last:
                return yaml.load(f_curr, Loader=SafeLoader), yaml.load(f_last, Loader=SafeLoader)


    # DeSOTA API Monitor
    #   > Get child models and remove desota tools (IGNORE_MODELS)
    def grab_all_user_models(self, ignore_models=IGNORE_MODELS) -> list:
        all_user_models = []
        if not self.user_models:
            return all_user_models
        self.__init__(ignore_update=True)
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
            select_task = requests.post(API_URL, data=data, timeout=30)
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
                        #print(file_type)
                        if file_type == "text":
                            # cprint(f'text select on 0', debug)   
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
                                    #print(file_type)
                                    if file_type == "text":
                                        # cprint(f'text select on 0', debug)   
                                        model_request_dict['dep_args'][dep_id]['text_prompt'] = str(file_value)
                                    elif file_type in ['image', 'video', 'audio', 'file']:
                                        model_request_dict['dep_args'][dep_id][file_type] = {}
                                        model_request_dict['dep_args'][dep_id][file_type]['file_name'] = str(file_value)
                                        model_request_dict['dep_args'][dep_id][file_type]['file_url'] = f"{API_UP}/{file_value}"
                                    else:
                                        model_request_dict['dep_args'][dep_id][file_type] = str(file_value)
                                            
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
            _model_serv = self.serv_conf["services_params"][model_id][USER_SYS]
        else:
            _model_serv = self.serv_conf["services_params"][ _model_params["parent_model"] ][USER_SYS]

        _model_starter = os.path.join(USER_PATH, _model_serv["service_path"], _model_serv["starter"]) if _model_serv["starter"] else None
        if not _model_starter:
            return
        
        if DEBUG or USER_SYS=="lin":
            cprint(f'Model start cmd:\n\t{_model_starter}', DEBUG)
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
        
        _model_serv = _model_params[USER_SYS]

        _model_stoper = os.path.join(USER_PATH, _model_serv["service_path"], _model_serv["stoper"]) if _model_serv["stoper"] else None
        if not _model_stoper:
            return None
        
        if DEBUG or USER_SYS=="lin":
            cprint(f'Model stop cmd:\n\t{_model_stoper}', DEBUG)
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

    #   > Create Model(s) installer for reinstalation
    def create_model_reinstalation(self, model_ids) -> str:
        # 1 - INIT + Scripts HEADER
        if USER_SYS == "win":
            '''I'm a windows nerd!'''
            # Init
            target_path = os.path.join(DESOTA_ROOT_PATH, f"tmp_model_install{int(time.time())}.bat")
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
            derunner_status_path = os.path.join(APP_PATH, "executables", "Windows", "derunner.status.bat")
            _tmp_file_lines += [
                ":wait_derunner_stop\n",
                f'FOR /F "tokens=*" %%g IN (\'{derunner_status_path} /nopause\') do (SET derunner_status=%%g)\n',
                "IF %derunner_status% EQU SERVICE_RUNNING GOTO wait_derunner_stop\n"
            ]
        elif USER_SYS=="lin":
            '''I know what i'm doing '''
            # Init
            target_path = os.path.join(DESOTA_ROOT_PATH, f"tmp_model_install{int(time.time())}.bash")
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
        for _model in model_ids:
            _asset_sys_params=self.serv_conf["services_params"][_model][USER_SYS]
            _asset_uninstaller = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["uninstaller"])
            _uninstaller_bn = os.path.basename(_asset_uninstaller)
            _tmp_uninstaller = os.path.join(USER_PATH, f'{int(time.time())}{_uninstaller_bn}')
            if os.path.isfile(_asset_uninstaller):
                _tmp_file_lines += [
                    f"{_log_prefix}Uninstalling '{_model}'...>>{LOG_PATH}\n",
                    f"{_copy}{_asset_uninstaller} {_tmp_uninstaller}\n",
                    f'{_start_cmd}{_tmp_uninstaller} {" ".join(_asset_sys_params["uninstaller_args"] if "uninstaller_args" in _asset_sys_params and _asset_sys_params["uninstaller_args"] else [])}{f" /automatic {USER_PATH}" if USER_SYS=="win" else " -a" if USER_SYS=="lin" else ""}\n',
                    f'{_rm}{_tmp_uninstaller} {_noecho}\n'
                ]


        # 3 - Download + Uncompress to target folder <- Required Models
        for _count, _model in enumerate(model_ids):
            _asset_params=self.last_serv_conf["services_params"][_model]
            _asset_sys_params=_asset_params[USER_SYS]
            _asset_repo=_asset_params["source_code"]
            _asset_commit=_asset_sys_params["commit"]
            _asset_project_dir = os.path.join(USER_PATH, _asset_sys_params["install_dir"] if "install_dir" in _asset_sys_params else _asset_sys_params["project_dir"])
            _tmp_repo_dwnld_path=os.path.join(USER_PATH, f"DeRunner_Dwnld_{_count}.zip")
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
            if os.path.isfile(_asset_setup):
                _tmp_file_lines += [
                    f"{_log_prefix}Installing '{_model}'... >>{LOG_PATH}\n",
                    f'{_start_cmd}{_asset_setup} {" ".join(_asset_sys_params["setup_args"] if "setup_args" in _asset_sys_params and _asset_sys_params["setup_args"] else [])}\n'
                ]


        # 5 - Start `run_constantly` Models <- Required Models
        for _model in model_ids:
            if _model == "desotaai/derunner":
                continue
            _asset_params=self.last_serv_conf["services_params"][_model]
            _asset_sys_params=_asset_params[USER_SYS]
            if _asset_params["run_constantly"]:
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
        
    
        ## 5.1 - after asset instalation!!
        #   > Update Services Config with params from Latest Services Config
        _app_after_model_reinstall = os.path.join(APP_PATH, "Tools", "after_model_reinstall.py")
        _tmp_file_lines.append(f'{_call}{_app_python} {_app_after_model_reinstall}{_noecho}\n')


        # Force DeRunner Restart
        if "desotaai/derunner" not in model_ids:
            _asset_sys_params=self.last_serv_conf["services_params"]["desotaai/derunner"][USER_SYS]
            _derunner_start = os.path.join(USER_PATH, _asset_sys_params["project_dir"], _asset_sys_params["execs_path"], _asset_sys_params["starter"])
            _tmp_file_lines += [
                f"{_log_prefix}Restarting DeRunner... >>{LOG_PATH}\n",
                f'{_start_cmd}{_derunner_start}\n'
            ]


        ## END OF FILE - Delete Bat at end of instalation 
        ### WINDOWS - retrieved from https://stackoverflow.com/a/20333152
        ### LINUX   - ...
        _tmp_file_lines.append('(goto) 2>nul & del "%~f0"\n'if USER_SYS == "win" else f'rm -rf {target_path}\n' if USER_SYS == "lin" else "")


        # 6 - Create Installer Bat
        with open(target_path, "w") as fw:
            fw.writelines(_tmp_file_lines)
        user_chown(target_path)
        return target_path

    #   > Request Model(s) reinstalation
    def request_model_reinstall(self, _reinstall_model, init=False):
        if init:
            # UPGRADE CONFIGURATIONS (Target: self.last_serv_conf)
            self.__init__()

        _reinstall_path = self.create_model_reinstalation(_reinstall_model)

        if not _reinstall_path:
            return None

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
        print(f" [ WARNING ] -> Model Reinstalation required:\n\tmodel: {_reinstall_model}\n\treinstall cmd: {' '.join(_reinstall_cmd)}")
        return 0
    
    #   > Check for upgrades
    def req_service_upgrade(self):
        # Timer check
        upgrade_timer = self.handle_upgrade_timer()
        if upgrade_timer != "go for it":
            return None
        

        delogger(f"[ INFO:{int(time.time())} ] - Searching for models upgrade.")
        # UPGRADE CONFIGURATIONS (Target: self.last_serv_conf)
        self.__init__()
        if not self.user_models:
            delogger(f"[ INFO ] - Models upgrade completed. Next upgrade in {int(UPG_FREQ/3600)}h")
            return None
        _upg_models = []
        for _model in list(self.user_models.keys()):
            curr_version = self.serv_conf["services_params"][_model][USER_SYS]["version"]
            last_version = self.last_serv_conf["services_params"][_model][USER_SYS]["version"]
            if curr_version != last_version:
                _upg_models.append(_model)
        if not _upg_models:
            self.handle_upgrade_timer(create=True)
            return None
        
        delogger(f"[ INFO:{int(time.time())} ] - Founded the following models to upgrade: {_upg_models}")
        req_reinstall = self.request_model_reinstall(_upg_models)
        if req_reinstall == 0:
            self.handle_upgrade_timer(create=True)
            return 0


    # Call Model Runner
    def call_model(self, model_req):
        # Create tmp model_req.yaml with request params for model runner
        _tmp_req_path = os.path.join(APP_PATH, f"tmp_model_req{int(time.time())}.yaml")
        with open(_tmp_req_path, 'w',) as fw:
            yaml.dump(model_req,fw,sort_keys=False)

        # Model Vars
        _model_id = model_req['task_model']                                             # Model Name
        _model_runner_param = self.serv_conf["services_params"][_model_id][USER_SYS]      # Model params from services.config.yaml
        _model_runner = os.path.join(USER_PATH, _model_runner_param["project_dir"], _model_runner_param["desota_runner"])          # Model runner path
        _model_runner_py = os.path.join(USER_PATH, _model_runner_param["python_path"])    # Python with model runner packages

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
                    exit(66)

                model_req = self.monitor_model_request(ignore_models=_ignore_models, debug=DEBUG)

                if not model_req:
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
                    exit(66)

if __name__ == "__main__":
    args = parser.parse_args()
    derunner_class = Derunner()
    # derunner_class.debug(args)
    derunner_class.mainloop(args)
