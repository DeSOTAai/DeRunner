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

api_key = "01e9b4cd0be07cbf719a1b88c161aabd83f35d1e5955716affea61744a197110"
api_url = "http://129.152.27.36/assistant/api.php"
api_up = "http://129.152.27.36/assistant/api_uploads"
i=0

models=['audio-classification-efficientat', 'whisper-small-en', 'coqui-tts-male', 'lllyasviel/sd-controlnet-seg-text-to-image','lllyasviel/sd-controlnet-openpose-text-to-image','lllyasviel/sd-controlnet-normal-text-to-image','lllyasviel/sd-controlnet-mlsd-text-to-image','lllyasviel/sd-controlnet-hed-text-to-image','lllyasviel/sd-controlnet-depth-text-to-image','lllyasviel/sd-controlnet-canny-text-to-image','lllyasviel/sd-controlnet-openpose-control','lllyasviel/sd-controlnet-normal-control','lllyasviel/sd-controlnet-mlsd-control','lllyasviel/sd-controlnet-hed-control','lllyasviel/sd-controlnet-canny-control','lllyasviel/sd-controlnet-text','clip','basic-vid2vid','basic-txt2vid','watch-video','talking-heads','clip-2','clip-2']

while True:
    i+=1
    print(f"Running...{i}")
    selected_task = False
    for model in models:
        data = {
            "api_key":api_key,
            "model":model
        }
        task = requests.post(api_url, data=data)
        if task.status_code==200:
            data = {
                "api_key":api_key,
                "model":model,
                "select_task":i
            }
            select_task = requests.post(api_url, data=data)
            if select_task.status_code==200:
                print(f"MODEL: {model}")
                cont = str(select_task.content.decode('UTF-8'))
                #print(cont)
                try:
                    selected_task = json.loads(cont)
                except:
                    print(cont)


                    cont = cont.replace("FIXME!!!", "")
                    #cont = cont.replace("\n", "")
                    #cont = cont.replace(r'\\\\', "")
                    #cont = cont.replace("\\\\\\", "")
                    #cont = cont.replace('\\', '')
                    #cont = cont.replace("\n", "")
                    #cont = cont.replace("\\", "")
                    

                    try:
                        selected_task = json.loads(cont)
                    except:
                        selected_task = "error"
                        print(selected_task)
                if "error" not in selected_task:
                    print(selected_task)

                    #print(selected_task['task'])
                    filename = 0
                    task_dic = ast.literal_eval(str(selected_task['task']))
                    if(task_dic != int(0)):
                        for file_type in task_dic:
                            #print(file_type)
                            if file_type in ["image", "audio", "video"]:
                                filename=str(task_dic[file_type])
                                file_url = f"{api_up}/{filename}"
                                print(f"file name select 1: {filename}")
                            else:
                                print(f'text select on 0')
                                task_text_prompt=str(task_dic[file_type])
                                #file_url = f"{api_up}/{filename}"
                            if "text" in task_dic:
                                print(f'text select on 1')
                                task_text_prompt = task_dic['text']

                            
                        task_type = selected_task['type']
                        task_dep = str(selected_task['dep']).replace("\\\\n", "").replace("\\", "")
                        task_dep = ast.literal_eval(task_dep)
                        print(f"task type is {task_type}")
                        print(f"task deps are {task_dep}")
                        #if json.loads(str(task_dep.decode('UTF-8'))):
                        if task_dep != "[-1]":
                            print("Dependencies:")
                            #deps = json.loads(str(task_dep.decode('UTF-8')))
                            for dep in task_dep:
                                try:
                                    dep_dic = json.loads(str(task_dep[dep]))
                                except:
                                    dep_dic = find_json(str(task_dep[dep]))
                                    dep_dic = json.loads(dep_dic)
                                try:
                                    for file_type in dep_dic:
                                        filename=str(dep_dic[file_type])
                                        file_url = f"{api_up}/{filename}"
                                        print(filename)
                                except:
                                    if not filename:
                                        print("no filename found")
                                        
                        else:
                            print("No Dependencies!")
                        #exit()
                        text_prompt = task_text_prompt

                    else:
                        print(f"No task for {model}!")
                        #exit()
                    print(task_text_prompt)

                else:
                    #error = selected_task['error']
                    print(f"Error: {selected_task}")
                    selected_task = False
        if selected_task and "error" not in selected_task:
            break

    if not selected_task:
        print("Byeeee")
        continue

    send_task_url=f"{api_url}?api_key={api_key}&model={model}&send_task="+selected_task['id']

    #send_task_data = {
    #    "api_key":api_key,
    #    "model":model
    #}
    #sendTask = requests.post(api_url, data=data)

    if task_type in ["image-to-image", "seg-image-to-image", "canny-image-to-image", "softedge-image-to-image", "lines-image-to-image", "normals-image-to-image", "pose-image-to-image"]:
        if (not filename.endswith('.jpg')) and (not filename.endswith('.png')) and (not filename.endswith('.png')) and (not filename.endswith('.gif')) and (not filename.endswith('.bmp')):
            text_prompt = filename
            task_type = task_type.replace("image-to-", "text-to-")
    

    if task_type == "video-to-text":
        ##TODO Extend obv

        filename = os.path.basename(file_url)
        file_ext = os.path.splitext(filename)[1]
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        in_filename = f'video-to-text.{file_ext}'
        in_filepath = os.path.join(dir_path, in_filename)
        out_filepath = os.path.join(dir_path, "video-to-text.txt")

        with requests.get(file_url, stream=True) as r:
            with open(in_filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        #TODO IS AROUND HERE
        #USE FFMPEG TO SPLIT EXEC SO USER CAN HAS UPDATES
        #Execute
        check_call('py -3.10 D:/ask-anything/video_chat_with_stablelm/app_ke.py --path="' + str(in_filepath) + '" --json="' + str(out_filepath)+'"')
        # Prepare the files to be uploaded
        file_paths = [str("video-to-text.txt")]
        files = []
        for path in file_paths:
            files.append(('upload[]', open(out_filepath, 'rb')))
        #print(selected_task['id'])
        send_task = requests.post(url = send_task_url, files=files)
        print(send_task.content)
        if send_task.status_code==200:
            print("TASK OK!")



    if task_type == "automatic-speech-recognition":
        ##TODO

        filename = os.path.basename(file_url)
        file_ext = os.path.splitext(filename)[1]
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tpath = os.path.join(dir_path, 'temp')
        tpath = os.path.join(tpath, 'automatic-speech-recognition-2')
        in_filename = f'automatic-speech-recognition.{file_ext}'
        in_filepath = os.path.join(dir_path, in_filename)
        in2_filepath = os.path.join(dir_path, f'automatic-speech-recognition-2.wav')
        output = os.path.join(dir_path, f'automatic-speech-recognition.txt')
        out_filepath = os.path.join(tpath, "automatic-speech-recognition-2.vtt")

        with requests.get(file_url, stream=True) as r:
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

    if task_type == "audio-classification":

        dir_path = os.path.dirname(os.path.realpath(__file__))
        in_filename = 'audio-classification.wav'
        in_filepath = os.path.join(dir_path, in_filename)
        out_filepath = os.path.join(dir_path, "audio-classification.txt")

        with requests.get(file_url, stream=True) as r:
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


    if task_type == "text-to-speech":
        ##TODO

        #filename = os.path.basename(file_url)
        #file_ext = os.path.splitext(filename)[1]
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        output = os.path.join(dir_path, f'output-tts.wav')

        print(check_call('git-bash docker ps -a -q  --filter ancestor=ghcr.io/coqui-ai/tts:latest'))
        qout = output
        model = "tts_models/en/vctk/vits"
        textquery=str(text_prompt).strip()
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



    if task_type == "text-to-image":
        flow = "normal_flow"
        model_id = "text-to-image"
        check_call(f'python3 ./main.py --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        
    if task_type == "text-to-video":
        flow = "normal_flow"
        model_id = "text-to-video"
        check_call(f'python3 ./main.py --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        
    if task_type == "image-to-text":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(file_url)
        model_id = "image-to-text"
        check_call(f'python3 ./main.py --img_url="{file_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        
    if task_type == "object-detection":

        dir_path = os.path.dirname(os.path.realpath(__file__))
        in_filename = 'object-detection.jpg'
        in_filepath = os.path.join(dir_path, in_filename)

        with requests.get(file_url, stream=True) as r:
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

    if task_type == "video-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(file_url)
        model_id = "video-to-video"
        check_call(f'python3 ./main.py --vid_url="{file_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        


    if task_type == "image-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(file_url)
        model_id = "image-to-video"
        check_call(f'python3 ./main.py --vid_url="{file_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        


    if task_type == "portrait-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(file_url)
        model_id = "talking-head"
        check_call(f'python3 ./main.py --img_url="{file_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        

    if task_type == "portrait-to-video":
        flow = "normal_flow"
        print(selected_task)
        print("with deps:")
        print(file_url)
        model_id = "talking-head"
        check_call(f'python3 ./main.py --img_url="{file_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        

    if task_type in ["image-to-image", "seg-image-to-image", "canny-image-to-image", "softedge-image-to-image", "lines-image-to-image", "normals-image-to-image", "pose-image-to-image", "mediapipe-face-control", "content-shuffle-control"]:
        if task_type == 'image-to-image':
            if model == 'lllyasviel/sd-controlnet-openpose-control':
                model_id = task_type = "pose-image-to-image"            
            if model == 'lllyasviel/sd-controlnet-normal-control':
                model_id = task_type = "normals-image-to-image"
            if model == 'lllyasviel/sd-controlnet-mlsd-control':
                model_id = task_type = "lines-image-to-image"
            if model == 'lllyasviel/sd-controlnet-hed-control':
                model_id = task_type = "softedge-image-to-image"
            if model == 'lllyasviel/sd-controlnet-canny-control':
                model_id = task_type = "canny-image-to-image"
        else:
            model_id = task_type
        post_temp_url = f"{api_url}?api_key={api_key}&model={model}&update_task=1&send_task="+selected_task['id']
        print(f"phase1 {model_id} preprocessor")
        check_call(f'python3 ./main.py --img_url="{file_url}" --posturl="{post_temp_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        
        time.sleep(1)
        print("phase 2, controlnet to image")
        

        data = {
            "api_key":api_key,
            "model":model,
            "select_task":i
        }
        select_task = requests.post(api_url, data=data)
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
                            filename=str(task_dic[file_type])
                        else:
                            task_text_prompt=str(task_dic[file_type])
                        #file_url = f"{api_up}/{filename}"
                        task_text_prompt = ""
                        if "text" in task_dic:
                            task_text_prompt = task_dic['text']
                        print(filename)
                    #task_type = selected_task['type']
                    task_dep = selected_task['dep']
                    print(f"task type is {task_type}")
                    print(f"task deps are {task_dep}")
                    #if json.loads(str(task_dep.decode('UTF-8'))):
                    #if task_dep != "[-1]":
                    #    print("Dependencies:")
                    #    #deps = json.loads(str(task_dep.decode('UTF-8')))
                    #    for dep in task_dep:
                    #        dep_dic = json.loads(str(task_dep[dep]))
                    #        for file_type in dep_dic:
                    #            filename=str(dep_dic[file_type])
                    #            file_url = f"{api_up}/{filename}"
                    #            print(filename)
                    #else:
                    #    print("No Dependencies!")
                    #exit()
                    #text_prompt = task_text_prompt
                    with open('tasks.json') as file:
                        # Load the JSON data
                        data = json.load(file)

                    # Access the object's filename
                    filename = data['filename']
                    ctrl_url = f"{api_up}/{filename}"

                    if task_type == "canny-image-to-image":
                        model_id="image-to-image-canny"
                    if task_type == "softedge-image-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if task_type == "depth-image-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if task_type == "lines-image-to-image":
                        model_id="image-to-image-control-line"
                    if task_type == "normals-image-to-image":
                        model_id="image-to-image-control-normal"
                    if task_type == "pose-image-to-image":
                        model_id="image-to-image-control-pose"
                    if task_type == "seg-image-to-image":
                        model_id="image-to-image-control-segment"

                    check_call(f'python3 ./main.py --img_url="{file_url}"  --control_dep_url="{ctrl_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        

    if task_type in ["seg-text-to-image", "canny-text-to-image", "softedge-text-to-image", "lines-text-to-image", "normals-text-to-image", "pose-text-to-image", "seg-text-to-image", "canny-text-to-image", "depth-text-to-image", "hed-text-to-image", "mlsd-text-to-image","normal-text-to-image","openpose-text-to-image"]:

        if task_type == "canny-text-to-image":
            model_id="canny-image-to-image"
        if task_type == "hed-text-to-image":
            model_id="softedge-image-to-image"
        if task_type == "softedge-text-to-image":
            model_id="softedge-image-to-image"
        if task_type == "depth-text-to-image":
            model_id="softedge-image-to-image"
        if task_type == "lines-text-to-image":
            model_id="image-to-image-control-line"
        if task_type == "normals-text-to-image":
            model_id="image-to-image-control-normal"
        if task_type == "openpose-text-to-image":
            model_id="image-to-image-control-pose"
        if task_type == "pose-text-to-image":
            model_id="image-to-image-control-pose"
        if task_type == "seg-text-to-image":
            model_id="seg-image-to-image"

        post_temp_url = f"{api_url}?api_key={api_key}&model={model}&update_task=1&send_task="+selected_task['id']
        print(f"phase1 {model_id} preprocessor")
        check_call(f'python3 ./main.py --img_url="{file_url}" --posturl="{post_temp_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        
        time.sleep(1)
        print("phase 2, controlnet to image")

        data = {
            "api_key":api_key,
            "model":model,
            "select_task":i
        }
        select_task = requests.post(api_url, data=data)
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
                            filename=str(task_dic[file_type])
                        else:
                            task_text_prompt=str(task_dic[file_type])
                        #file_url = f"{api_up}/{filename}"
                        task_text_prompt = ""
                        if "text" in task_dic:
                            task_text_prompt = task_dic['text']
                        print(filename)
                    task_type = selected_task['type']
                    task_dep = selected_task['dep']
                    print(f"task type is {task_type}")
                    print(f"task deps are {task_dep}")
                    #if json.loads(str(task_dep.decode('UTF-8'))):
                    #if task_dep != "[-1]":
                    #    print("Dependencies:")
                    #    #deps = json.loads(str(task_dep.decode('UTF-8')))
                    #    for dep in task_dep:
                    #        dep_dic = json.loads(str(task_dep[dep]))
                    #        for file_type in dep_dic:
                    #            filename=str(dep_dic[file_type])
                    #            file_url = f"{api_up}/{filename}"
                    #            print(filename)
                    #else:
                    #    print("No Dependencies!")
                    #exit()
                    #text_prompt = task_text_prompt

                    with open('tasks.json') as file:
                        # Load the JSON data
                        data = json.load(file)

                    # Access the object's filename
                    filename = data['filename']
                    ctrl_url = f"{api_up}/{filename}"



                    if task_type == "canny-text-to-image":
                        model_id="image-to-image-canny"
                    if task_type == "softedge-text-to-image" or task_type == "hed-text-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if task_type == "depth-text-to-image":
                        model_id="image-to-image-control-soft-edge"
                    if task_type == "lines-text-to-image":
                        model_id="image-to-image-control-line"
                    if task_type == "normals-text-to-image":
                        model_id="image-to-image-control-normal"
                    if task_type == "pose-text-to-image":
                        model_id="image-to-image-control-pose"
                    if task_type == "seg-text-to-image":
                        model_id="image-to-image-control-segment"

                    check_call(f'python3 ./main.py --img_url="{file_url}" --control_dep_url="{ctrl_url}" --posturl="{send_task_url}" --model_id="{model_id}" --text-prompt="{text_prompt}"')        


            
            

   


    #if task_type == "openpose-text-to-image":
    #if task_type == "seg-text-to-image":


    
#        exit()


    #exit()

    #check_call("python3 ./main.py")
    print(f"Will start this thing again hehe!")
    
    time.sleep(1)


