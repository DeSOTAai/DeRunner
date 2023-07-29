import time
import requests
from subprocess import check_output
from subprocess import check_call, call, CalledProcessError
from subprocess import Popen, CREATE_NEW_CONSOLE
import ast
import json
import io
import os
import re
import shutil

def find_json(s):
    s = s.replace("\'", "\"")
    start = s.find("{")
    end = s.rfind("}")
    res = s[start:end+1]
    res = res.replace("\n", "")
    return res
    
print("Runner Up!")

API_KEY = "01e9b4cd0be07cbf719a1b88c161aabd83f35d1e5955716affea61744a197110"
API_URL = "http://129.152.27.36/assistant/api.php"
API_UP = "http://129.152.27.36/assistant/api_uploads"
DEBUG = False
I=0

models=['audio-classification-efficientat', 'whisper-small-en', 'coqui-tts-male', 'lllyasviel/sd-controlnet-seg-text-to-image','lllyasviel/sd-controlnet-openpose-text-to-image','lllyasviel/sd-controlnet-normal-text-to-image','lllyasviel/sd-controlnet-mlsd-text-to-image','lllyasviel/sd-controlnet-hed-text-to-image','lllyasviel/sd-controlnet-depth-text-to-image','lllyasviel/sd-controlnet-canny-text-to-image','lllyasviel/sd-controlnet-openpose-control','lllyasviel/sd-controlnet-normal-control','lllyasviel/sd-controlnet-mlsd-control','lllyasviel/sd-controlnet-hed-control','lllyasviel/sd-controlnet-canny-control','lllyasviel/sd-controlnet-text','clip','basic-vid2vid','basic-txt2vid','watch-video','talking-heads','clip-2','clip-2']

# Conditional print
def cprint(query, condition):
    if condition:
        print(query)

# Monitor API Model Request
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
            "select_task":i
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
                    for file_type in task_dic:
                        if file_type in ["image", "audio", "video"]:
                            selected_filename=str(task_dic[file_type])
                        else:
                            task_text_prompt=str(task_dic[file_type])
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
                    for file_type in task_dic:
                        if file_type in ["image", "audio", "video"]:
                            selected_filename=str(task_dic[file_type])
                        else:
                            task_text_prompt=str(task_dic[file_type])
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

# Monitor API Model Request 
def monitor_model_request(debug=False):
    global models, I
    I+=1
    
    cprint(f"Running...{I}", debug) # Conditional Print

    selected_task = False
    
    model_request_dict = {
        "task_type": None,      # TASK VARS
        "task_model": None,
        "task_dep": None,
        "task_args": None,
        "task_id": None,
        "filename": None,       # FILE VARS
        "file_url": None,
        "text_prompt": None     # TXT VAR
    }
    
    for model in models:
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
                print(f"[ WARNING ] -> API Model Request fail for model `{model}`")
                selected_task = False
                continue
            
            cprint(selected_task, debug)     # Conditional Print
            #cprint(selected_task['task'], debug)
            model_request_dict['filename'] = 0
            task_dic = ast.literal_eval(str(selected_task['task']))
            if(task_dic != int(0)):
                for file_type in task_dic:
                    #print(file_type)
                    if file_type in ["image", "audio", "video"]:
                        model_request_dict['filename']=str(task_dic[file_type])
                        model_request_dict['file_url'] = f"{API_UP}/{model_request_dict['filename']}"
                        cprint(f"file name select 1: {model_request_dict['filename']}", debug)   # Conditional Print
                    else:
                        cprint(f'text select on 0', debug)   # Conditional Print
                        task_text_prompt=str(task_dic[file_type])
                        #model_request_dict['file_url'] = f"{API_UP}/{model_request_dict['filename']}"
                    if "text" in task_dic:
                        cprint(f'text select on 1', debug)   # Conditional Print
                        task_text_prompt = task_dic['text']

                    
                model_request_dict["task_type"] = selected_task['type']
                task_dep = str(selected_task['dep']).replace("\\\\n", "").replace("\\", "")
                task_dep = ast.literal_eval(task_dep)
                model_request_dict["task_dep"] = task_dep
                cprint(f"task type is {model_request_dict['task_type']}", debug)     # Conditional Print
                cprint(f"task deps are {task_dep}", debug)   # Conditional Print
                #if json.loads(str(task_dep.decode('UTF-8'))):
                if task_dep != "[-1]":
                    cprint("Dependencies:", debug)   # Conditional Print
                    #deps = json.loads(str(task_dep.decode('UTF-8')))
                    for dep in task_dep:
                        try:
                            dep_dic = json.loads(str(task_dep[dep]))
                        except:
                            dep_dic = find_json(str(task_dep[dep]))
                            dep_dic = json.loads(dep_dic)
                        try:
                            for file_type in dep_dic:
                                model_request_dict['filename']=str(dep_dic[file_type])
                                model_request_dict['file_url'] = f"{API_UP}/{model_request_dict['filename']}"
                                cprint(model_request_dict['filename'], debug)    # Conditional Print
                        except:
                            if not model_request_dict['filename'] and debug:
                                print("no filename found")

                cprint("No Dependencies!", debug)    # Conditional Print
                #exit()
                model_request_dict['text_prompt'] = task_text_prompt

            cprint(f"No task for {model}!", debug)   # Conditional Print
            #exit()

            cprint(task_text_prompt, debug)  # Conditional Print

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

    if model_request_dict["task_type"] in ["image-to-image", "seg-image-to-image", "canny-image-to-image", "softedge-image-to-image", "lines-image-to-image", "normals-image-to-image", "pose-image-to-image"]:
        if (not model_request_dict['filename'].endswith('.jpg')) and (not model_request_dict['filename'].endswith('.png')) and (not model_request_dict['filename'].endswith('.png')) and (not model_request_dict['filename'].endswith('.gif')) and (not model_request_dict['filename'].endswith('.bmp')):
            model_request_dict['text_prompt'] = model_request_dict['filename']
            model_request_dict["task_type"] = model_request_dict["task_type"].replace("image-to-", "text-to-")
    
    return model_request_dict

# Main Loop
def main():    
    print("Runner Up!")
    
    while True:
        # clear()
        model_req = monitor_model_request(DEBUG)
        if model_req == None:
            continue
        print(f"[ INFO ] -> Incoming Model Request:\n{json.dumps(model_req, indent=2)}")

        run_models(model_req)

if __name__ == "__main__":
    main()
