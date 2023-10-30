import os
import json
import yaml
from yaml.loader import SafeLoader



# :: os.getcwd() = C:\users\[user]\Desota\DeRunner\Tools
# WORKING_FOLDER = os.getcwd()
WORKING_FOLDER = os.path.dirname(os.path.realpath(__file__))
USER_PATH = "\\".join(WORKING_FOLDER.split("\\")[:-3])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")

CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
USER_CONF_PATH = os.path.join(CONFIG_PATH, "user.config.yaml")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")
LAST_SERV_CONF_PATH = os.path.join(CONFIG_PATH, "latest_services.config.yaml")

SERVICE_TOOLS_PATH = os.path.join(CONFIG_PATH, "Services")
SERVICES_START_PATH = os.path.join(SERVICE_TOOLS_PATH, "models_starter.bat")
SERVICES_STOP_PATH = os.path.join(SERVICE_TOOLS_PATH, "models_stopper.bat")

# Open the file and load the file
if not os.path.isfile(USER_CONF_PATH) or not os.path.isfile(SERV_CONF_PATH) or not os.path.isfile(LAST_SERV_CONF_PATH):
    print(f" [USER_CONF_PATH] -> {USER_CONF_PATH}")
    print(f" [SERV_CONF_PATH] -> {SERV_CONF_PATH}")
    print(f" [LAST_SERV_CONF_PATH] -> {LAST_SERV_CONF_PATH}")
    raise EnvironmentError()

with open(USER_CONF_PATH) as f:
    USER_CONF = yaml.load(f, Loader=SafeLoader)
with open(SERV_CONF_PATH) as f:
    SERV_CONF = yaml.load(f, Loader=SafeLoader)
with open(LAST_SERV_CONF_PATH) as f:
    LAST_SERV_CONF = yaml.load(f, Loader=SafeLoader)

USER_MODELS = USER_CONF['models']
USER_SYSTEM = USER_CONF['system']


# IGNORE_MODELS = ["desotaai/derunner"]

# # retieved from https://stackoverflow.com/a/11995662  && https://stackoverflow.com/a/10052222 && https://stackoverflow.com/a/40388766
# GET_ADMIN = [
#     "net session >NUL 2>NUL\n",
#     "IF %errorLevel% NEQ 0 (\n",
#     "\tgoto UACPrompt\n",
#     ") ELSE (\n",
#     "\tgoto gotAdmin\n",
#     ")\n",
#     ":UACPrompt\n",
#     'powershell -Command "Start-Process -Wait -Verb RunAs -FilePath \'%0\' -ArgumentList \'am_admin\'" \n',
#     "exit /B\n",
#     ":gotAdmin\n",
#     'pushd "%CD%"\n',
#     f'CD /D "{DESOTA_ROOT_PATH}"\n'
# ]

# #   > Update Models Starter for Run constantly models
# def upd_model_start():
#     if USER_SYSTEM == "win":
#         # 2 - Get Admin Previleges 
#         _tmp_file_lines = [
#             "@ECHO OFF\n"
#         ]
#         _tmp_file_lines += GET_ADMIN

#         _exist_run_constantly_model = False
#         for model_id, model_v in USER_MODELS.items():

#             service_params = LAST_SERV_CONF["services_params"][model_id] if LAST_SERV_CONF["services_params"][model_id][USER_SYSTEM]["version"] == model_v else SERV_CONF["services_params"][model_id]
            
#             _model_param_run_constantly = service_params["run_constantly"]
#             if not _model_param_run_constantly:
#                 continue

#             if not _exist_run_constantly_model:
#                 _exist_run_constantly_model = True

#             _model_serv_path = service_params[USER_SYSTEM]["service_path"]
#             _model_serv_start = service_params[USER_SYSTEM]["starter"]
#             if _model_serv_start:
#                 _model_start_path = os.path.join(USER_PATH, _model_serv_path, _model_serv_start)
                
#                 _tmp_file_lines.append(f"start /B /WAIT {_model_start_path}\n")

#         if not _exist_run_constantly_model:
#             if os.path.isfile(SERVICES_START_PATH):
#                 os.remove(SERVICES_START_PATH)
#             return
        
#         _tmp_file_lines.append("exit\n")

#         # 4 - Create Starter Bat
#         with open(SERVICES_START_PATH, "w") as fw:
#             fw.writelines(_tmp_file_lines)
            
#         return
            
# #   > Update Models Stoper
# def upd_model_stop():
#     if USER_SYSTEM == "win":
#         # 2 - Get Admin Previleges 
#         _tmp_file_lines = [
#             "@ECHO OFF\n"
#         ]
#         _tmp_file_lines += GET_ADMIN
        
#         _exist_model2stop = False
#         for model_id, model_v in USER_MODELS.items():
#             service_params = LAST_SERV_CONF["services_params"][model_id] if LAST_SERV_CONF["services_params"][model_id][USER_SYSTEM]["version"] == model_v else SERV_CONF["services_params"][model_id]
            
#             if not _exist_model2stop:
#                 _exist_model2stop = True

#             _model_serv_path = service_params[USER_SYSTEM]["service_path"]
#             _model_serv_stop = service_params[USER_SYSTEM]["stoper"]
#             if _model_serv_stop:
#                 _model_stop_path = os.path.join(USER_PATH, _model_serv_path, _model_serv_stop)
                
#                 _tmp_file_lines.append(f"start /B /WAIT {_model_stop_path}\n")

#         if not _exist_model2stop:
#             if os.path.isfile(SERVICES_STOP_PATH):
#                 os.remove(SERVICES_STOP_PATH)
#             return
        
#         _tmp_file_lines.append("exit\n")

#         # 4 - Create Starter Bat
#         with open(SERVICES_STOP_PATH, "w") as fw:
#             fw.writelines(_tmp_file_lines)

#         return
    
#   > Update Services Config with params from Latest Services Config
def upd_serv_conf():
    _res_serv_conf = SERV_CONF.copy()
    _res_serv_conf["services_params"]={}
    for model_id, model_v in USER_MODELS.items():
        if LAST_SERV_CONF["services_params"][model_id][USER_SYSTEM]["version"] == model_v or model_id not in _res_serv_conf["services_params"]:
            _res_serv_conf["services_params"][model_id] = LAST_SERV_CONF["services_params"][model_id]
        if "child_models" in _res_serv_conf["services_params"][model_id] and _res_serv_conf["services_params"][model_id]["child_models"]:
            for child in _res_serv_conf["services_params"][model_id]["child_models"]:
                if child in LAST_SERV_CONF["services_params"]:
                    _res_serv_conf["services_params"][child] = LAST_SERV_CONF["services_params"][child]

    with open(SERV_CONF_PATH, 'w',) as fw:
        yaml.dump(_res_serv_conf,fw,sort_keys=False)

    return
        

def main():
    # upd_model_start()
    # upd_model_stop()
    upd_serv_conf()

if __name__ == "__main__":
    main()