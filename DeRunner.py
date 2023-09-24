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



# Monitor API Model Request 
# TODO - MOVE TO dynamic Model runner
'''
def run_models(model_request_dict):
    selected_task = model_request_dict['selected_task']
    send_task_url = f"{API_URL}?api_key={API_KEY}&model={model}&send_task="+selected_task['id']

    if model_request_dict["task_type"] == "video-to-text":
        ##TODO Extend obv

        base_filename = os.path.basename(model_request_dict['file_url'])
        file_ext = os.path.splitext(base_filename)[1]
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        in_filename = f'video-to-text.{file_ext}'
        in_filepath = os.path.join(dir_path, in_filename)
        out_filepath = os.path.join(dir_path, "video-to-text.txt")

        with requests.get(model_request_dict['file_url'], stream=True) as r:
            with open(in_filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        #TODO IS AROUND HERE
        #USE FFMPEG TO SPLIT EXEC SO USER CAN HAS UPDATES
        #Execute
        check_call('py -3.10 D:/ask-anything/video_chat_with_stablelm/app_ke.py --path="' + str(in_filepath) + '" --json="' + str(out_filepath)+'"')
        # Prepare the files to be uploaded
        file_paths = [str("video-to-text.txt")]
        files = []
        for _ in file_paths:
            files.append(('upload[]', open(out_filepath, 'rb')))
        #print(selected_task['id'])
        send_task = requests.post(url = send_task_url, files=files)
        print(send_task.content)
        if send_task.status_code==200:
            print("TASK OK!")



    if model_request_dict["task_type"] == "automatic-speech-recognition":
        ##TODO

        base_filename = os.path.basename(model_request_dict['file_url'])
        file_ext = os.path.splitext(base_filename)[1]
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tpath = os.path.join(dir_path, 'temp')
        tpath = os.path.join(tpath, 'automatic-speech-recognition-2')
        in_filename = f'automatic-speech-recognition.{file_ext}'
        in_filepath = os.path.join(dir_path, in_filename)
        in2_filepath = os.path.join(dir_path, f'automatic-speech-recognition-2.wav')
        output = os.path.join(dir_path, f'automatic-speech-recognition.txt')
        out_filepath = os.path.join(tpath, "automatic-speech-recognition-2.vtt")

        with requests.get(model_request_dict['file_url'], stream=True) as r:
            with open(in_filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)


        try:
            # Run the command and raise an error if the return code is non-zero
            check_call(f"ffmpeg -i {in_filepath} -vn -acodec pcm_s16le -ar 44100 -ac 2 -hide_banner -loglevel error -y {in2_filepath}")
            has_audio = True
        except:
            has_audio = False

        try:
            check_call(f'python3 whisper_run.py --input=automatic-speech-recognition-2.wav')
            time.sleep(0.5)
            if(os.path.exists(out_filepath)):
                os.replace(out_filepath, output)
            # Prepare the files to be uploaded
            file_paths = [str(output)]
            files = []
            for path in file_paths:
                files.append(('upload[]', open(output, 'rb')))
            #print(selected_task['id'])
            send_task = requests.post(url = send_task_url, files=files)
            print(send_task.content)
            if send_task.status_code==200:
                print("TASK OK!")
                #exit()
        except:
            print("ERROR")

    if model_request_dict["task_type"] == "audio-classification":

        dir_path = os.path.dirname(os.path.realpath(__file__))
        in_filename = 'audio-classification.wav'
        in_filepath = os.path.join(dir_path, in_filename)
        out_filepath = os.path.join(dir_path, "audio-classification.txt")

        with requests.get(model_request_dict['file_url'], stream=True) as r:
            with open(in_filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        check_call(f'py -3.9 ../efficientat/inference.py --cuda --model_name=mn40_as_ext --audio_path="{in_filepath}" --output="{out_filepath}"')
        
        # Prepare the files to be uploaded
        file_paths = [str("audio-classification.txt")]
        files = []
        for path in file_paths:
            files.append(('upload[]', open(out_filepath, 'rb')))
        #print(selected_task['id'])
        send_task = requests.post(url = send_task_url, files=files)
        print(send_task.content)
        if send_task.status_code==200:
            print("TASK OK!")


    if model_request_dict["task_type"] == "text-to-speech":
        ##TODO

        #base_filename = os.path.basename(model_request_dict['file_url'])
        #file_ext = os.path.splitext(base_filename)[1]
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        output = os.path.join(dir_path, f'output-tts.wav')

        print(check_call('git-bash docker ps -a -q  --filter ancestor=ghcr.io/coqui-ai/tts:latest'))
        qout = output
        model = "tts_models/en/vctk/vits"
        textquery=str(model_request_dict['text_prompt']).strip()
        mysql_quote = "`"
        textquery = re.sub("[\"']", mysql_quote, textquery)
        
        #then reinitiate
        call='docker run --name rebel_neptune --rm -it -p 5002:5002 --gpus all --entrypoint /bin/bash ghcr.io/coqui-ai/tts '
        Popen(str(call), creationflags=CREATE_NEW_CONSOLE)
        server ='docker exec -it rebel_neptune tts --text "'+str(textquery)+'" --model_name "'+str(model)+'"  --speaker_idx "p230" --out_path ./output-tts.wav'

        print(check_call(str(server)))
        
        print(Popen("docker cp rebel_neptune:/root/output-tts.wav "+str(qout)))

        time.sleep(0.2)
        # Prepare the files to be uploaded
        file_paths = [str(output)]
        files = []
        for path in file_paths:
            files.append(('upload[]', open(output, 'rb')))
        #print(selected_task['id'])
        send_task = requests.post(url = send_task_url, files=files)
        print(send_task.content)
        if send_task.status_code==200:
            print("TASK OK!")
            #exit()



    if model_request_dict["task_type"] == "text-to-image":
        flow = "normal_flow"
        model_id = "text-to-image"
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        
    if model_request_dict["task_type"] == "text-to-video":
        flow = "normal_flow"
        model_id = "text-to-video"
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        
    if model_request_dict["task_type"] == "image-to-text":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(model_request_dict['file_url'])
        model_id = "image-to-text"
        file_url_tmp = model_request_dict['file_url']
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --img_url="{file_url_tmp}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        
    if model_request_dict["task_type"] == "object-detection":

        dir_path = os.path.dirname(os.path.realpath(__file__))
        in_filename = 'object-detection.jpg'
        in_filepath = os.path.join(dir_path, in_filename)

        with requests.get(model_request_dict['file_url'], stream=True) as r:
            with open(in_filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        check_call(f'py -3.9 ./object_detect.py {in_filepath} rtmdet_tiny_8xb32-300e_coco.py --weights rtmdet_tiny_8xb32-300e_coco_20220902_112414-78e30dcc.pth --device cuda:0')
        
        #out_dir = os.path.join(dir_path, "/outputs/vis/")
        out_path = os.path.join("./outputs/vis/", "object-detection.jpg")
        # Prepare the files to be uploaded
        file_paths = [str("object-detection.jpg")]
        files = []
        for path in file_paths:
            files.append(('upload[]', open(out_path, 'rb')))
        #print(selected_task['id'])
        send_task = requests.post(url = send_task_url, files=files)
        print(send_task.content)
        if send_task.status_code==200:
            print("TASK OK!")        

    if model_request_dict["task_type"] == "video-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(model_request_dict['file_url'])
        model_id = "video-to-video"
        file_url_tmp = model_request_dict['file_url']
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --vid_url="{file_url_tmp}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        


    if model_request_dict["task_type"] == "image-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(model_request_dict['file_url'])
        model_id = "image-to-video"
        file_url_tmp = model_request_dict['file_url']
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --vid_url="{file_url_tmp}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        


    if model_request_dict["task_type"] == "portrait-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(model_request_dict['file_url'])
        model_id = "talking-head"
        file_url_tmp = model_request_dict['file_url']
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --img_url="{file_url_tmp}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        

    if model_request_dict["task_type"] == "portrait-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(model_request_dict['file_url'])
        model_id = "talking-head"
        file_url_tmp = model_request_dict['file_url']
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --img_url="{file_url_tmp}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        

    if model_request_dict["task_type"] in ["image-to-image", "seg-image-to-image", "canny-image-to-image", "softedge-image-to-image", "lines-image-to-image", "normals-image-to-image", "pose-image-to-image", "mediapipe-face-control", "content-shuffle-control"]:
        if model_request_dict["task_type"] == 'image-to-image':
            if model == 'lllyasviel/sd-controlnet-openpose-control':
                model_id = model_request_dict["task_type"] = "pose-image-to-image"            
            if model == 'lllyasviel/sd-controlnet-normal-control':
                model_id = model_request_dict["task_type"] = "normals-image-to-image"
            if model == 'lllyasviel/sd-controlnet-mlsd-control':
                model_id = model_request_dict["task_type"] = "lines-image-to-image"
            if model == 'lllyasviel/sd-controlnet-hed-control':
                model_id = model_request_dict["task_type"] = "softedge-image-to-image"
            if model == 'lllyasviel/sd-controlnet-canny-control':
                model_id = model_request_dict["task_type"] = "canny-image-to-image"
        else:
            model_id = model_request_dict["task_type"]
        post_temp_url = f"{API_URL}?api_key={API_KEY}&model={model}&update_task=1&send_task="+selected_task['id']
        print(f"phase1 {model_id} preprocessor")
        file_url_tmp = model_request_dict['file_url']
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --img_url="{file_url_tmp}" --posturl="{post_temp_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        
        time.sleep(1)
        print("phase 2, controlnet to image")
        

        data = {
            "api_key":API_KEY,
            "model":model,
            "select_task":I
        }
        select_task = requests.post(API_URL, data=data)
        if select_task.status_code==200:
            cont = str(select_task.content.decode('UTF-8'))
            #print(cont)
            selected_task = json.loads(cont)
            if "error" not in selected_task:
                print(selected_task)
                #print(selected_task['task'])

                task_dic = ast.literal_eval(str(selected_task['task']))
                if(task_dic != int(0)):
                    for file_type, file_value in task_dic.items():
                        if file_type in ["image", "audio", "video"]:
                            selected_filename=str(file_value)
                        else:
                            task_text_prompt=str(file_value)
                        #selected_file_url = f"{API_UP}/{selected_filename}"
                        task_text_prompt = ""
                        if "text" in task_dic:
                            task_text_prompt = task_dic['text']
                        print(selected_filename)
                    #task_type = selected_task['type']
                    task_dep = selected_task['dep']
                    print(f"task type is {model_request_dict['task_type']}")
                    print(f"task deps are {task_dep}")
                    #if json.loads(str(task_dep.decode('UTF-8'))):
                    #if task_dep != "[-1]":
                    #    print("Dependencies:")
                    #    #deps = json.loads(str(task_dep.decode('UTF-8')))
                    #    for dep in task_dep:
                    #        dep_dic = json.loads(str(task_dep[dep]))
                    #        for file_type in dep_dic:
                    #            selected_filename=str(dep_dic[file_type])
                    #            selected_file_url = f"{API_UP}/{selected_filename}"
                    #            print(selected_filename)
                    #else:
                    #    print("No Dependencies!")
                    #exit()
                    # text_prompt = task_text_prompt # Atention >model_request_dict['text_prompt']< text_prompt deprecated
                    with open('tasks.json') as file:
                        # Load the JSON data
                        data = json.load(file)

                    # Access the object's filename
                    task_filename = data['filename']
                    ctrl_url = f"{API_UP}/{task_filename}"

                    if model_request_dict["task_type"] == "canny-image-to-image":
                        model_id="image-to-image-canny"
                    if model_request_dict["task_type"] == "softedge-image-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if model_request_dict["task_type"] == "depth-image-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if model_request_dict["task_type"] == "lines-image-to-image":
                        model_id="image-to-image-control-line"
                    if model_request_dict["task_type"] == "normals-image-to-image":
                        model_id="image-to-image-control-normal"
                    if model_request_dict["task_type"] == "pose-image-to-image":
                        model_id="image-to-image-control-pose"
                    if model_request_dict["task_type"] == "seg-image-to-image":
                        model_id="image-to-image-control-segment"

                    file_url_tmp = model_request_dict['file_url']
                    text_prompt_tmp = model_request_dict['text_prompt']
                    check_call(f'python3 ./main.py --img_url="{file_url_tmp}"  --control_dep_url="{ctrl_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        

    if model_request_dict["task_type"] in ["seg-text-to-image", "canny-text-to-image", "softedge-text-to-image", "lines-text-to-image", "normals-text-to-image", "pose-text-to-image", "seg-text-to-image", "canny-text-to-image", "depth-text-to-image", "hed-text-to-image", "mlsd-text-to-image","normal-text-to-image","openpose-text-to-image"]:

        if model_request_dict["task_type"] == "canny-text-to-image":
            model_id="canny-image-to-image"
        if model_request_dict["task_type"] == "hed-text-to-image":
            model_id="softedge-image-to-image"
        if model_request_dict["task_type"] == "softedge-text-to-image":
            model_id="softedge-image-to-image"
        if model_request_dict["task_type"] == "depth-text-to-image":
            model_id="softedge-image-to-image"
        if model_request_dict["task_type"] == "lines-text-to-image":
            model_id="image-to-image-control-line"
        if model_request_dict["task_type"] == "normals-text-to-image":
            model_id="image-to-image-control-normal"
        if model_request_dict["task_type"] == "openpose-text-to-image":
            model_id="image-to-image-control-pose"
        if model_request_dict["task_type"] == "pose-text-to-image":
            model_id="image-to-image-control-pose"
        if model_request_dict["task_type"] == "seg-text-to-image":
            model_id="seg-image-to-image"

        post_temp_url = f"{API_URL}?api_key={API_KEY}&model={model}&update_task=1&send_task="+selected_task['id']
        print(f"phase1 {model_id} preprocessor")
        file_url_tmp = model_request_dict['file_url']
        text_prompt_tmp = model_request_dict['text_prompt']
        check_call(f'python3 ./main.py --img_url="{file_url_tmp}" --posturl="{post_temp_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        
        time.sleep(1)
        print("phase 2, controlnet to image")

        data = {
            "api_key":API_KEY,
            "model":model,
            "select_task":i
        }
        select_task = requests.post(API_URL, data=data)
        if select_task.status_code==200:
            cont = str(select_task.content.decode('UTF-8'))
            print(cont)
            selected_task = json.loads(cont)
            if "error" not in selected_task:
                print(selected_task)
                #print(selected_task['task'])

                task_dic = ast.literal_eval(str(selected_task['task']))
                if(task_dic != int(0)):
                    for file_type, file_value in task_dic:
                        if file_type in ["image", "audio", "video"]:
                            selected_filename=str(file_value)
                        else:
                            task_text_prompt=str(file_value)
                        #file_url = f"{API_UP}/{selected_filename}"
                        task_text_prompt = ""
                        if "text" in task_dic:
                            task_text_prompt = task_dic['text']
                        print(selected_filename)
                    selected_task_type = selected_task['type']
                    task_dep = selected_task['dep']
                    print(f"task type is {selected_task_type}")
                    print(f"task deps are {task_dep}")
                    #if json.loads(str(task_dep.decode('UTF-8'))):
                    #if task_dep != "[-1]":
                    #    print("Dependencies:")
                    #    #deps = json.loads(str(task_dep.decode('UTF-8')))
                    #    for dep in task_dep:
                    #        dep_dic = json.loads(str(task_dep[dep]))
                    #        for file_type in dep_dic:
                    #            selected_filename=str(dep_dic[file_type])
                    #            file_url = f"{API_UP}/{selected_filename}"
                    #            print(selected_filename)
                    #else:
                    #    print("No Dependencies!")
                    #exit()
                    #text_prompt = task_text_prompt # Atention >model_request_dict['text_prompt']< text_prompt deprecated

                    with open('tasks.json') as file:
                        # Load the JSON data
                        data = json.load(file)

                    # Access the object's filename
                    task_filename = data['filename']
                    ctrl_url = f"{API_UP}/{task_filename}"



                    if selected_task_type == "canny-text-to-image":
                        model_id="image-to-image-canny"
                    if selected_task_type == "softedge-text-to-image" or selected_task_type == "hed-text-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if selected_task_type == "depth-text-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if selected_task_type == "lines-text-to-image":
                        model_id="image-to-image-control-line"
                    if selected_task_type == "normals-text-to-image":
                        model_id="image-to-image-control-normal"
                    if selected_task_type == "pose-text-to-image":
                        model_id="image-to-image-control-pose"
                    if selected_task_type == "seg-text-to-image":
                        model_id="image-to-image-control-segment"

                    file_url_tmp = model_request_dict['file_url']
                    text_prompt_tmp = model_request_dict['text_prompt']
                    check_call(f'python3 ./main.py --img_url="{file_url_tmp}" --control_dep_url="{ctrl_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt_tmp}"')        


    #if model_request_dict["task_type"] == "openpose-text-to-image":
    #if model_request_dict["task_type"] == "seg-text-to-image":

    #        exit()

    #exit()

    #check_call("python3 ./main.py")
    print(f"Will start this thing again hehe!")
    
    time.sleep(1)
'''



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
            task = requests.post(API_URL, data=data)
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

        _model_starter = os.path.join(USER_PATH, _model_serv["service_path"], _model_serv["starter"])
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

        _model_stoper = os.path.join(USER_PATH, _model_serv["service_path"], _model_serv["stoper"])
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
        
        return _ret_code


    # Main DeRunner Loop
    def mainloop(self, args) -> None:
        # Handshake - Service checker
        if args.handshake:
            print('{"status":"ready"}')
            return 0
        
        # Print Configurations
        print("Runner Up!")
        print(f"[ INFO ] -> Configurations:\n{json.dumps(self.user_conf, indent=2)}")

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
                print("*"*80)
                print(f"[ INFO ] -> Incoming Model Request:\n{json.dumps(model_req, indent=2)}")

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
                error_level = 8
                error_msg = f"DeRunner CRITICAL FAIL: {e}"
                _reinstall_model = "desotaai/derunner"
                pass
            
            if error_level:
                error_url = f"{API_URL}?api_key={self.user_api_key}&model={model_req['task_model']}&send_task={model_req['task_id']}&error={error_level}&error_msg={error_msg}" 
                error_res = requests.post(url = error_url)
                print(f"[ INFO ] -> DeSOTA ERROR Upload:\n\tURL: {error_url}\n\tRES: {json.dumps(error_res.json(), indent=2)}")
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
