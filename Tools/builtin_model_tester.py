import sys, os, time, json, ast
import yaml, validators

import subprocess, requests, traceback
from subprocess import check_output
from subprocess import check_call, call, CalledProcessError
from subprocess import Popen
try: 
    from subprocess import CREATE_NEW_CONSOLE
except:
    pass

from yaml.loader import SafeLoader
from desota import detools
DEBUG = True

USER_SYS = detools.get_platform()

# :: os.getcwd() = C:\users\[user]\Desota\DeRunner\Tools
# WORKING_FOLDER = os.getcwd()
WORKING_FOLDER = os.path.dirname(os.path.realpath(__file__))
if USER_SYS == "win":
    path_split = str(WORKING_FOLDER).split("\\")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "\\".join(path_split[:desota_idx])
elif USER_SYS == "lin":
    path_split = str(WORKING_FOLDER).split("/")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "/".join(path_split[:desota_idx])

DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
APP_PATH = os.path.join(DESOTA_ROOT_PATH, "DeRunner")
LOG_PATH = os.path.join(DESOTA_ROOT_PATH, "demanager.log")
TMP_PATH=os.path.join(DESOTA_ROOT_PATH, "tmp")
if not os.path.isdir(TMP_PATH):
    os.mkdir(TMP_PATH)
    detools.user_chown(TMP_PATH)

CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")
#   > Return services.config.yaml(write if not ignore_update)
def get_services_config(config_path):
    with open( config_path ) as f_curr:
        return yaml.load(f_curr, Loader=SafeLoader)
SERV_PARAMS = {}
import argparse
parser = argparse.ArgumentParser()
# MODEL ID
parser.add_argument("-m", "--model", 
                    help='Model to be tested',
                    type=str,
                    required=True)
# EXPERT - Auto-Complete --input-query
parser.add_argument("-e", "--expert", 
                    nargs='?',
                    const='', default='',
                    help='[OPTIONAL] Model Expert',
                    type=str)
# USER QUERY - User text Request (UI Searchbar)
parser.add_argument("-iq", "--input-query",
                    nargs='?',
                    const='', default='',
                    help='[OPTIONAL] User Input Query. Default list for each Expert',
                    type=str)
# COMMON INPUT TYPES:
#   file [DEFAULT]
#   text
#   image
#   video
#   audio
parser.add_argument("-it", "--input-type",
                    nargs='?',
                    const='file', default='file',
                    help='[OPTIONAL] Choose between ["audio", "image", "video", "text"]. Default "file". type "special" only works for selected experts and require `--input-dict` argument',
                    type=str)
# COMMON INPUT FILE, accepts:
#   file_path: for development
#   file_url : for deploy (Required for Model Publish)
parser.add_argument("-if", "--input-file", 
                    nargs='?',
                    const='', default='',
                    help='[OPTION 1] Pass file path | url to test model. Works for the majority of experts. By calling this argument will be ignored `--input-dict`')
# SPECIAL INPUT ARGS, used by special types args experts (eg. question-answering)
parser.add_argument("-id", "--input-dict",
                    nargs='?',
                    const={}, default={},
                    help='[OPTION 2] Pass model parameters {"input_type1":"input_content1", "input_type2":"input_content2", ...}. Only works for selected experts. By calling this argument will be ignored `--input-type` and `--input-file` arguments',
                    type=ast.literal_eval)
# TARGET PATH OS TEST REPORT
parser.add_argument("-rf", "--report-file", 
                    help='Test report path | url as json file',
                    type=str)
parser.add_argument("-sp", "--service-params",
                    nargs='?',
                    const='', default='',
                    help=f'[OPTIONAL] DeSOTA Service Parameters yaml. By default is read {SERV_CONF_PATH}',
                    type=dict)

# Utils Funcs
#   > Log to demanager.log
def delogger(query):
    if not os.path.isfile(LOG_PATH):
        with open(LOG_PATH, "w") as fw:
            fw.write(f"File Forced Creation by DeRunner Built-in Model Tester\n")

    with open(LOG_PATH, "a") as fa:
        if isinstance(query, str) or isinstance(query, int) or isinstance(query, float):
            fa.write(f"{query}\n")
        elif isinstance(query, list):
            fa.writelines(query)
        elif isinstance(query, dict):
            fa.write(json.dumps(query, indent=2))
            fa.write("\n")
    detools.user_chown(LOG_PATH)


# Simulate `monitor_model_request` method from DeRunner.py
#   > Default User Queries for Experts
def get_expert_query(expert):
    match expert:
        case "image-modification":
            return "Modify the content of this image, be creative"
        case "image-generation":
            return "Create an image with full artistic liberty"
        case "image-analysis":
            return "Describe the content of this image"

        case "video-modification":
            return "Modify the content of this video, be creative"
        case "video-generation":
            return "Create a video with full artistic liberty"
        case "video-analysis":
            return "Describe the content of this video"

        case "audio-generation":
            return "Modify the content of this audio, be creative"
        case "audio-recognition":
            return "Describe the content of this audio"

        case "question-answering":
            return "Contextualize"
        case "text-generation":
            return "Create a text history with full artistic liberty"
        case "conversational":
            return "Expand about this subject"
        case "translation":
            return "Translate the following"
        case "summarization":
            return "Sumarize the following"

        case "web-scraper":
            return "Describe the content of this webpage"
        case "document-analysis":
            return "Describe the content of this document"
        case "file-conversion":
            return "Convert this file"
        case _:
            return f"Behave as a {expert} model"

#   > Construct model_request_dict
def get_model_request_dict(model, expert, input_query, input_type, input_idx, input_dict):
    if not input_query:
        input_query = get_expert_query(expert)
    
    model_request_dict = {
        "task_type": "not_defined",      # TASK VARS
        "task_model": model,
        "task_dep": "not_aplied4test",
        "task_args": None,
        "task_id": "not_aplied4test",
    }
    # INPUT VARS
    if input_dict:
        input_dict["text_prompt"] = input_query
        model_request_dict["input_args"] = input_dict
    else:
        try:
            input_idx = ast.literal_eval(input_idx)
        except:
            pass
        if isinstance(input_idx, str):
            input_idx = [input_idx]
        input_file = []
        for in_f in input_idx:
            if validators.url(in_f):
                print("IM URL")
                input_file.append(in_f)
            else:
                if os.path.isfile(in_f):
                    input_file.append(in_f)
                else:
                    input_file_pth = os.path.join(USER_PATH, in_f)
                    if not os.path.isfile(input_file_pth):
                        print("IM RAW")
                        input_file.append(in_f)
                    else:
                        input_file.append(input_file_pth)                    

        if input_type in ["text"]:
            model_request_dict["input_args"] = {
                "text_prompt": [input_query]+input_file
            }
        else:
            #does model have input_arg dict?
            try:
                assert model_request_dict["input_args"]
            except:
                model_request_dict["input_args"]={} #here we create it if not
            try:
                assert model_request_dict["input_args"][input_type]
            except:
                model_request_dict["input_args"][input_type] = []
            for _file in input_file:
                file_basename = os.path.basename(_file)
                model_request_dict["input_args"][input_type].append(
                    {
                        "file_name": file_basename,
                        "file_url": input_file[0]
                    }
                )
            model_request_dict["input_args"]["text_prompt"] = [input_query]

    return model_request_dict


# Handle Model Service
#   > Start Service
def start_model_serv(model_id) -> None:
    global SERV_PARAMS
    _model_params = SERV_PARAMS[model_id]

    if not _model_params["submodel"]:
        _model_serv = _model_params[USER_SYS]
    else:
        _model_serv = SERV_PARAMS[ _model_params["parent_model"] ][USER_SYS]

    _model_starter = os.path.join(USER_PATH, _model_serv["project_dir"], _model_serv["execs_path"], _model_serv["starter"]) if _model_serv["starter"] else None
    if not _model_starter:
        return
    
    if DEBUG or USER_SYS=="lin":
        start_cmd = ["bash", _model_starter] if USER_SYS=="lin" else [_model_starter]
        print(f'Model start cmd:\n\t{" ".join(start_cmd)}')
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
def stop_model_serv(model_id) -> None:
    global SERV_PARAMS
    _model_params = SERV_PARAMS[model_id]

    if _model_params["submodel"]:
        _model_params = SERV_PARAMS[ _model_params["parent_model"] ]
    
    if _model_params["run_constantly"]:
        return
    
    _model_serv = _model_params[USER_SYS]

    _model_stoper = os.path.join(USER_PATH, _model_serv["project_dir"], _model_serv["execs_path"], _model_serv["stoper"]) if _model_serv["stoper"] else None
    if not _model_stoper:
        return None
    
    if DEBUG or USER_SYS=="lin":
        stop_cmd = ["bash", _model_stoper] if USER_SYS=="lin" else [_model_stoper]
        print(f'Model stop cmd:\n\t{" ".join(stop_cmd)}')
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


# Call Model Runner
def call_model(model_req, result_file):
    global SERV_PARAMS
    # Create tmp model_req.yaml with request params for model runner
    _tmp_req_path = os.path.join(TMP_PATH, f"tmp_model_req{int(time.time())}.yaml")
    with open(_tmp_req_path, 'w',) as fw:
        yaml.dump(model_req,fw,sort_keys=False)

    # Model Vars
    _model_id = model_req['task_model']                                             # Model Name
    _model_runner_param = SERV_PARAMS[_model_id][USER_SYS]      # Model params from services.config.yaml
    _model_runner = os.path.join(USER_PATH, _model_runner_param["project_dir"], _model_runner_param["desota_runner"])          # Model runner path
    _model_runner_py = os.path.join(USER_PATH, _model_runner_param["python_path"])    # Python with model runner packages
    _model_requirements = os.path.join(USER_PATH, _model_runner_param["pyrequirements"])
    _model_isTool = (SERV_PARAMS[_model_id]["service_type"] == "tool")
    # API Response URLs
    _model_res_url = result_file
    
    # Pip Install Requirements ~ NSSM BUGFIX
    if USER_SYS == "win" and _model_isTool:
        _pipInstall_cmd = [
            _model_runner_py, "-m", 
            "pip", "install", 
            "-r", _model_requirements
        ]
        _sproc = Popen( 
            _pipInstall_cmd,
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            encoding='utf-8',
        )
        while True:
            _ret_code = _sproc.poll()
            if _ret_code != None:
                delogger(f"[ DEBUG ] -> Pip Install stdout: {json.dumps(_sproc.stdout.readlines(), indent=2)}")
                break
            continue

    # Start / Wait Model
    # retrieved from https://stackoverflow.com/a/62226026
    _modelCall_cmd = [
        _model_runner_py, _model_runner, 
        "--model_req", _tmp_req_path, 
        "--model_res_url", _model_res_url
    ]
    print(f'[ INFO ] -> Model runner cmd:\n\t{" ".join(_modelCall_cmd)}', DEBUG)
    delogger(f'[ INFO ] ->Model runner cmd:\n\t{" ".join(_modelCall_cmd)}')
    if _model_isTool:
        _sproc = Popen(
            _modelCall_cmd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8',
        )
    else:
        _sproc = Popen( _modelCall_cmd )
    # TODO: implement model timeout
    while True:
        _ret_code = _sproc.poll()
        if _ret_code != None:
            if _model_isTool:
                delogger(f"[ DEBUG ] -> Process stdout: {json.dumps(_sproc.stdout.readlines(), indent=2)}")
            break
        continue

    if os.path.isfile(_tmp_req_path):
        os.remove(_tmp_req_path)

    print(f"[ INFO ] -> Model DEV `{model_req['task_model']}` returncode = {_ret_code}")
    delogger(f"[ INFO ] -> Model DEV `{model_req['task_model']}` returncode = {_ret_code}")
    
    return _ret_code


def main(args):
    global SERV_PARAMS
    _service_params = args.service_params
    _expert = args.expert
    _model = args.model
    _input_query = args.input_query
    _input_type = args.input_type
    _input_file = args.input_file
    _input_dict = args.input_dict
    _report_file = args.report_file
    
    if _service_params:
        SERV_PARAMS = get_services_config(_service_params)
    else:
        SERV_PARAMS = get_services_config(SERV_CONF_PATH)["services_params"]
    
    if _model not in SERV_PARAMS:
        print(f"[ ERROR ] -> Coulnd't find {_model} in Services Params:", json.dumps(SERV_PARAMS, indent=2))
    
    try:
        if not (_input_file and _input_dict):
            test_args = SERV_PARAMS[_model][USER_SYS]["test_args"]
            _input_query = test_args["query"]
            _input_type = test_args["type"]
            _input_file = test_args["file"]
            _input_dict = test_args["raw_dict"]
    except:
        print(f"[ ERROR ] -> Coulnd't Retrieve {_model} test args from Services Params:", json.dumps(SERV_PARAMS, indent=2))

    if not _report_file: # Consider Main DeRunner Default Test
        # TODO: Send Report to DeSOTA
        clean_model_name = _model.replace("/", "_").replace("\\", "_")
        name_split = clean_model_name.split("_")
        if len(name_split) > 1:
            clean_model_name = "_".join(name_split[1:])
        _report_file = os.path.join(DESOTA_ROOT_PATH, f"{clean_model_name}_report.json")
    
    print("BuiltInTester [_service_params]:", _service_params)
    print("BuiltInTester [_expert]:", _expert)
    print("BuiltInTester [_model]:", _model)
    print("BuiltInTester [_input_query]:", _input_query)
    print("BuiltInTester [_input_type]:", _input_type)
    print("BuiltInTester [_input_file]:", _input_file)
    print("BuiltInTester [_input_dict]:", _input_dict)
    print("BuiltInTester [_report_file]:", _report_file)

    delogger(f"BuiltInTester [_service_params]: {_service_params}")
    delogger(f"BuiltInTester [_expert]: {_expert}")
    delogger(f"BuiltInTester [_model]: {_model}")
    delogger(f"BuiltInTester [_input_query]: {_input_query}")
    delogger(f"BuiltInTester [_input_type]: {_input_type}")
    delogger(f"BuiltInTester [_input_file]: {_input_file}")
    delogger(f"BuiltInTester [_input_dict]: {_input_dict}")
    delogger(f"BuiltInTester [_report_file]: {_report_file}")

    try: # Run Test
        model_req = get_model_request_dict(_model, _expert, _input_query, _input_type, _input_file, _input_dict)
        print("*"*80)
        delogger("*"*80)
        print(f"[ INFO ] -> Development Model Request:\n{json.dumps(model_req, indent=2)}")
        delogger(f"[ INFO ] -> Development Model Request:\n{json.dumps(model_req, indent=2)}")
        start_model_serv(_model)
        model_res = call_model(model_req, _report_file)
        match model_res:
            case 0:
                print("[ SUCESS ] -> Model Completed without errors!")
                delogger("[ SUCESS ] -> Model Completed without errors!")
                exit(0)
            case 1:
                print("[ ERROR ] -> Model INPUT ERROR")
                delogger("[ ERROR ] -> Model INPUT ERROR")
            case 2:
                print("[ ERROR ] -> Model OUTPUT ERROR")
                delogger("[ ERROR ] -> Model OUTPUT ERROR")
            case 3:
                print("[ ERROR ] -> Publish Result ERROR")
                delogger("[ ERROR: ] -> Publish Result ERROR")
            case _:
                print(f"[ ERROR ] -> Undefined Model ERROR. Return Code: {model_res}")
                delogger(f"[ ERROR ] -> Undefined Model ERROR. Return Code: {model_res}")
        
    except Exception as e:
        print(f'[ CRITICAL FAIL ] -> DeRunner Fail INFO:\n  Exception: {e}\n  {traceback.format_exc()}')
        delogger([
            f"[ CRITICAL FAIL ] -> Re-Install DeRunner: \n",
            f"  Exception: {e}\n",
            f"  {traceback.format_exc()}\n"
        ])
        pass
    exit(1)

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)