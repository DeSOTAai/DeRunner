import os
import json
import yaml
from yaml.loader import SafeLoader


# :: os.getcwd() = C:\users\[user]\Desota\DeRunner\Tools
# WORKING_FOLDER = os.getcwd()
WORKING_FOLDER = os.path.dirname(os.path.realpath(__file__))
USER_PATH = os.path.sep.join(WORKING_FOLDER.split(os.path.sep)[:-3])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")

CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
USER_CONF_PATH = os.path.join(CONFIG_PATH, "user.config.yaml")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")
LAST_SERV_CONF_PATH = os.path.join(CONFIG_PATH, "latest_services.config.yaml")


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
    
#   > Update Services Config with params from Latest Services Config
def upd_serv_conf():
    _res_serv_conf = SERV_CONF.copy()
    _res_serv_conf["services_params"]={}
    for model_id, model_v in USER_MODELS.items():
        if LAST_SERV_CONF["services_params"][model_id]["submodel"]:
            continue
        if LAST_SERV_CONF["services_params"][model_id][USER_SYSTEM]["version"] == model_v or model_id not in _res_serv_conf["services_params"]:
            _res_serv_conf["services_params"][model_id] = LAST_SERV_CONF["services_params"][model_id] 
            print(" [ SET SERV CONF ] -> Append:", model_id)
        if "child_models" in _res_serv_conf["services_params"][model_id] and _res_serv_conf["services_params"][model_id]["child_models"]:
            for child in _res_serv_conf["services_params"][model_id]["child_models"]:
                if child in LAST_SERV_CONF["services_params"]:
                    _res_serv_conf["services_params"][child] = LAST_SERV_CONF["services_params"][child]
                    print(" [ SET SERV CONF ] -> Append:", child)


    with open(SERV_CONF_PATH, 'w',) as fw:
        yaml.dump(_res_serv_conf,fw,sort_keys=False)

    return
        

def main():
    # upd_model_start()
    # upd_model_stop()
    upd_serv_conf()

if __name__ == "__main__":
    main()