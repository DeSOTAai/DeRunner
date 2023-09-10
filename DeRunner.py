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
DEBUG = True

# :: os.getcwd() = C:\users\[user]\Desota\DeRunner
WORKING_FOLDER = os.getcwd()
USER_PATH = "\\".join(WORKING_FOLDER.split("\\")[:-2])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
APP_PATH = os.path.join(DESOTA_ROOT_PATH, "DeRunner")
CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
USER_CONF_PATH = os.path.join(CONFIG_PATH, "user.config.yaml")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")

# Open the file and load the file
if not os.path.isfile(USER_CONF_PATH) or not os.path.isfile(SERV_CONF_PATH):
    raise EnvironmentError()

with open(USER_CONF_PATH) as f:
    USER_CONF = yaml.load(f, Loader=SafeLoader)
with open(SERV_CONF_PATH) as f:
    SERV_CONF = yaml.load(f, Loader=SafeLoader)
API_KEY = USER_CONF['api_key']

API_URL = "http://129.152.27.36/assistant/api.php"
API_UP =  "http://129.152.27.36/assistant/api_uploads"

USER_MODELS = USER_CONF['models']
IGNORE_MODELS = ["desotaai/derunner"] # DeSOTA Tools Services that don't run with DeRunner

# MODEL_TO_METHOD = configs['model_to_method']

# models=['audio-classification-efficientat', 'whisper-small-en', 'coqui-tts-male', 'lllyasviel/sd-controlnet-seg-text-to-image','lllyasviel/sd-controlnet-openpose-text-to-image','lllyasviel/sd-controlnet-normal-text-to-image','lllyasviel/sd-controlnet-mlsd-text-to-image','lllyasviel/sd-controlnet-hed-text-to-image','lllyasviel/sd-controlnet-depth-text-to-image','lllyasviel/sd-controlnet-canny-text-to-image','lllyasviel/sd-controlnet-openpose-control','lllyasviel/sd-controlnet-normal-control','lllyasviel/sd-controlnet-mlsd-control','lllyasviel/sd-controlnet-hed-control','lllyasviel/sd-controlnet-canny-control','lllyasviel/sd-controlnet-text','clip','basic-vid2vid','basic-txt2vid','watch-video','talking-heads','clip-2','clip-2']




# Models Methods > DEPRECATED
'''
class ModelsRunner(object):
    # question-answering-large-dataset
    def run_neuralqa_qa(self, model_request_dict):
        print('Hello')
    
    # query-expansion
    def run_neuralqa_expansion(self, model_request_dict):
        print('Hello')

    # url-to-text
    def run_descraper_url(self, model_request_dict):
        # Time when grabed
        start_time = int(time.time())

        # API Response URL
        send_task_url = f"{API_URL}?api_key={API_KEY}&model={model_request_dict['task_model']}&send_task=" + model_request_dict['task_id']
        
        # File Path
        dir_path = os.path.dirname(os.path.realpath(__file__))
        out_filepath = os.path.join(dir_path, f"url-to-text_{start_time}.txt")
        
        # Descraper Request Preparation
        descraper_url = "http://127.0.0.1:8880/api/scraper"
        payload = {
            "url": model_request_dict["task_args"]['url'] if 'url' in model_request_dict["task_args"] else model_request_dict["task_args"]['text'],
            "html_text": True,
            "overwrite_files": False
        }
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Connection": "keep-alive",
            "Content-Type": "application/json; charset=UTF-8"
        }
        # Descraper Request
        print(f"[ INFO ] -> Descraper Request Payload:\n{json.dumps(payload, indent=2)}")
        descraper_response = requests.request("POST", descraper_url, json=payload, headers=headers)
        descraper_res = descraper_response.json()
        print(f"[ INFO ] -> Descraper Response:\n{json.dumps(descraper_res, indent=2)}")

        if descraper_response.status_code != 200:
            print(f"[ ERROR ] -> Descraper Request Failed (Info):\npayload:{json.dumps(payload, indent=2)}\nResponse Code:{descraper_response.status_code}")
            return False
        
        # DeSOTA API Response Preparation
        with open(out_filepath, 'w', encoding="utf-8") as fw:
            fw.write(descraper_res["html_text"] if "html_text" in descraper_res else json.dumps(descraper_res))
        files = []
        with open(out_filepath, 'rb') as fr:
            files.append(('upload[]', fr))
            # DeSOTA API Response Post
            send_task = requests.post(url = send_task_url, files=files)
            print(f"[ INFO ] -> DeSOTA API Upload:\n{json.dumps(send_task.json(), indent=2)}")
        # Delete temporary file
        os.remove(out_filepath)

        if send_task.status_code != 200:
            print(f"[ ERROR ] -> Descraper Post Failed (Info):\files: {files}\nResponse Code: {send_task.status_code}")
            return False
        
        print("TASK OK!")
        return True

    # html-to-text
    def run_descraper_html(self, model_request_dict):
        print('Hello')
'''


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
def cprint(query, condition):
    if condition:
        print(query)
#   > Get child models and remove desota tools (IGNORE_MODELS)
def grab_all_user_models():
    all_user_models = list(USER_MODELS.keys())
    for model in list(USER_MODELS.keys()):
        if model in IGNORE_MODELS:
            all_user_models.pop(all_user_models.index(model))
            continue

        _model_params = SERV_CONF["services_params"][model]
        _child_models = None if "child_models" not in _model_params and not _model_params["child_models"] else _model_params["child_models"]
        if _child_models:
            if isinstance(_child_models, str):
                _child_models = [_child_models]
            if isinstance(_child_models, list):
                for _child_model in _child_models:
                    if _child_model in SERV_CONF["services_params"] and _child_model not in all_user_models:
                        all_user_models.append(_child_model)
    return all_user_models

     
# DeRunner Methods
#   > Monitor API Model Request 
def monitor_model_request(debug=False):
    global I
    I+=1
    
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
    _all_user_models = grab_all_user_models()
                    
    cprint(f"[ INFO ] -> All User Models: {json.dumps(_all_user_models, indent=4)}", debug)

    if not _all_user_models:
        return None
    
    for model in _all_user_models:
        '''
        Send a POST request to API to get a task
            Return: `task`
        ''' 

        data = {
            "api_key":API_KEY,
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
            "api_key":API_KEY,
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
                cprint(f"task deps are {task_dep} {type(task_dep[0])}", debug)   # Conditional Print
                #if json.loads(str(task_dep.decode('UTF-8'))):
                if task_dep != [-1]:
                    cprint("Dependencies:", debug)   # Conditional Print
                    #deps = json.loads(str(task_dep.decode('UTF-8')))
                    model_request_dict['dep_args'] = {}
                    for dep in task_dep:
                        try:
                            dep_dic = json.loads(str(task_dep[dep]))
                        except:
                            try:
                                dep_dic = find_json(str(task_dep[dep]))                        
                            
                                dep_dic = json.loads(dep_dic)
                                model_request_dict['dep_args'][dep] = {}
                                for file_type, file_value in dep_dic.items():
                                    #print(file_type)
                                    if file_type in ['image', 'video', 'audio', 'file']:
                                        model_request_dict['dep_args'][dep][file_type] = {}
                                        model_request_dict['dep_args'][dep][file_type]['file_name'] = str(file_value)
                                        model_request_dict['dep_args'][dep][file_type]['file_url'] = f"{API_UP}/{file_value}"
                                    else:
                                        model_request_dict['dep_args'][dep][file_type] = str(file_value)
                                            
                            except:
                                if not model_request_dict['dep_args'] and debug:
                                    print("no filename found")
                    
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
    #    "api_key":API_KEY,
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
#   > Handle Model Service
def start_model_serv(model_id):
    _opsys = USER_CONF["system"]
    _model_params = SERV_CONF["services_params"][model_id]

    if not _model_params["submodel"]:
        _model_serv = SERV_CONF["services_params"][model_id][_opsys]
    else:
        _model_serv = SERV_CONF["services_params"][ _model_params["parent_model"] ][_opsys]

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
def stop_model_serv(model_id):
    _opsys = USER_CONF["system"]
    _model_params = SERV_CONF["services_params"][model_id]

    if not _model_params["submodel"]:
        _model_params = SERV_CONF["services_params"][model_id]
    else:
        _model_params = SERV_CONF["services_params"][ _model_params["parent_model"] ]
    
    if _model_params["run_constantly"]:
        return
    
    _model_serv = _model_params[_opsys]

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
#   > Call Model Runner
def call_model(model_req):
    # Create tmp model_req.yaml with request params for model runner
    _tmp_req_path = os.path.join(APP_PATH, f"tmp_model_req{int(time.time())}.yaml")
    with open(_tmp_req_path, 'w',) as fw:
        yaml.dump(model_req,fw,sort_keys=False)

    # Model Vars
    _opsys = USER_CONF["system"]                                                    # Operating system (win | lin | mac)
    _model_id = model_req['task_model']                                             # Model Name
    _model_runner_param = SERV_CONF["services_params"][_model_id][_opsys]           # Model params from services.config.yaml
    _model_runner = os.path.join(USER_PATH, _model_runner_param["runner"])          # Model runner path
    _model_runner_py = os.path.join(USER_PATH, _model_runner_param["runner_py"])    # Python with model runner packages

    # API Response URL
    _model_res_url = f"{API_URL}?api_key={API_KEY}&model={model_req['task_model']}&send_task=" + model_req['task_id']
    
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


# Main Loop
def main(args):
    # Handshake - Service checker
    if args.handshake:
        print('{"status":"ready"}')
        return 0
    
    print("Runner Up!")
    '''Get Configurations'''
    print(f"[ INFO ] -> Configurations:\n{json.dumps(USER_CONF, indent=2)}")
    while True:
        try:
            # clear()
            # TODO : Check for new installed models . Run Tester here
            model_req = monitor_model_request(False)
            if model_req == None:
                continue
            print("*"*80)
            print(f"[ INFO ] -> Incoming Model Request:\n{json.dumps(model_req, indent=2)}")

            start_model_serv(model_req['task_model'])
            
            model_res = call_model(model_req)

            # TODO : Handle process return code
            if model_res == 1:
                print(f"[ TODO ] -> Model INPUT ERROR (Write exec_state = 9)")
            elif model_res == 2:
                print(f"[ TODO ] -> Model OUTPUT ERROR (Retry in another server)")
            elif model_res == 3:
                # TODO: Is Possible here that server lost internet connectivity:
                #   - Test internet acess - Idle DeRunner until internet connection (STOP ALL DESOTA WHILE INDLING, START AFTER)
                #   - API Model Request TIMEOUT (additionally DeSOTA can ping server every 10 sec - 3 error ping consider server down [ DeRunner can handle this while model is running in backgroud inside `call_model()` ! ])
                print(f"[ TODO ] -> Write Result to DeSOTA ERROR (Retry in another server)")
            elif model_res != 0:
                raise ChildProcessError(model_req['task_model'])
            
            stop_model_serv(model_req['task_model'])

        except ChildProcessError as cpe:
            #cpe = model name
            # TODO: Inform DeSOTA API that this server can no longer continue this request!
            print(f"[ WARNING ] -> Re-Install Model in background: {cpe}")
            pass
        except ConnectionError as ce:
            print(f"[ WARNING ] -> DeRunner Lost Internet Acess: {ce}")
            pass
        except Exception as e:
            print(f"[ CRITICAL FAIL ] -> Re-Install DeRunner: {e}")
            pass
        # if DEBUG:
        #     break

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)