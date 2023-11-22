import os
import json
import yaml
from yaml.loader import SafeLoader
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-k", "--key", 
                    help='User Configs Key',
                    type=str)
parser.add_argument("-v", "--value", 
                    help='User Configs Value',
                    type=str)


# Get Configs
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
with open(LAST_SERV_CONF_PATH) as f:
    LAST_SERV_CONF = yaml.load(f, Loader=SafeLoader)

USER_MODELS = USER_CONF['models']
USER_SYSTEM = USER_CONF['system']


# Set User Configs
def main(args):
    user_config = USER_CONF

    # param "models" consist of the name of the model as key and is version as value
    if args.key == "models":
        # Get allready installed models
        _old_models = USER_MODELS
        # Instatiate result models
        _res_models = dict(_old_models)

        # Uninstall FLAG - DEPRECATED ( ONLY DEMANAGER OR DERUNNER TESTER CAN UNINSTALL)

        # Convert cmd arg into models dict
        _new_models = json.loads(args.value)
        if not _old_models:
            _old_models = {}
        for _model, _version in _new_models.items():
            _model_params = LAST_SERV_CONF["services_params"][_model]
            _model_w_childs = [_model]
            if "childs" in _model_params and _model_params["childs"]:
                if isinstance(_model_params["childs"], str):
                    _model_w_childs += [_model_params["childs"]]
                elif isinstance(_model_params["childs"], list):
                    _model_w_childs += _model_params["childs"]
            for _mwc in  _model_w_childs:
                if _mwc in _res_models:
                    if _res_models[_mwc] == _version:
                        continue
                    _res_models[_mwc] = _version
                    continue
                _res_models.update({_model:_version})
        # Update user_config `models`
        user_config[args.key] = _res_models
    else:
        user_config[args.key] = args.value
        
    with open(USER_CONF_PATH, 'w',) as fw:
        yaml.dump(user_config,fw,sort_keys=False)



if __name__ == "__main__":
    args = parser.parse_args()
    main(args)