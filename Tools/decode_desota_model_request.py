import os, sys
import time, requests
import re, shutil

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
# DeSOTA PATHS
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
#   > USER_PATH
if USER_SYS == "win":
    path_split = str(CURRENT_PATH).split("\\")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "\\".join(path_split[:desota_idx])
elif USER_SYS == "lin":
    path_split = str(CURRENT_PATH).split("/")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "/".join(path_split[:desota_idx])
def user_chown(path):
    '''Remove root previleges for files and folders: Required for Linux'''
    if USER_SYS == "lin":
        #CURR_PATH=/home/[USER]/Desota/DeRunner
        os.system(f"chown -R {USER} {path}")
    return
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
TMP_PATH=os.path.join(DESOTA_ROOT_PATH, "tmp")
if not os.path.isdir(TMP_PATH):
    os.mkdir(TMP_PATH)
    user_chown(TMP_PATH)

# UTILS
def get_url_from_str(string) -> list:
    # retrieved from https://www.geeksforgeeks.org/python-check-url-string/
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]
#
def retrieve_file_content(file_idx) -> str:
    if os.path.isfile(file_idx):
            with open(file_idx, 'r') as fr:
                return fr.read()
    file_url = get_url_from_str(file_idx)
    if len(file_url)==0:
        return file_idx
    file_url = file_url[0]
    file_ext = os.path.splitext(file_url)[1] if file_url else None
    if not file_url or not file_ext:
        return file_idx
    file_content = ""
    with  requests.get(file_idx, stream=True) as req_file:
        if req_file.status_code != 200:
            return file_idx
        
        if req_file.encoding is None:
            req_file.encoding = 'utf-8'

        for line in req_file.iter_lines(decode_unicode=True):
            if line:
                file_content += line
    return file_content
#
def download_file(file_idx, get_file_content=False) -> str:
    if get_file_content:
        return retrieve_file_content(file_idx)
    out_path = os.path.join(TMP_PATH, os.path.basename(file_idx))
    if os.path.isfile(file_idx):
        return file_idx
    file_url = get_url_from_str(file_idx)
    if not file_url:
        return file_idx
    file_ext = os.path.splitext(file_url[0])[1] if file_url else None
    if not file_url or not file_ext:
        return file_idx
    with requests.get(file_idx, stream=True) as r:
        if r.status_code != 200:
            return file_idx
        with open(out_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        user_chown(out_path)
    return out_path


# MODELS
# TODO: Get Deps Args
#   > TEXT
def get_request_text(model_request_dict) -> list:
    _req_text = None
    if 'query' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['query'], list):
            _req_text = []
            for query in model_request_dict["input_args"]['query']:
                _req_text.append(download_file(query, get_file_content=True))
    
    if 'text_prompt' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['text_prompt'], list):
            _req_text = []
            for text_prompt in model_request_dict["input_args"]['text_prompt']:
                _req_text.append(download_file(text_prompt, get_file_content=True))
    if not _req_text and 'file' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['file'], list):
            _req_text = []
            for file_idx in model_request_dict["input_args"]['file']:
                if "file_url" in file_idx:
                    _req_text.append(download_file(file_idx["file_url"], get_file_content=True))
    
    return _req_text

#   > AUDIO
def get_request_audio(model_request_dict, target_dist) -> list:
    audio_file = None
    if 'audio' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['audio'], list):
            audio_file = []
            for audio in model_request_dict["input_args"]['audio']:
                if "file_url" in audio:
                    audio_file.append(download_file(audio["file_url"], get_file_content=True))
    elif 'file' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['file'], list):
            audio_file = []
            for file_idx in model_request_dict["input_args"]['file']:
                if "file_url" in file_idx:
                    audio_file.append(download_file(file_idx["file_url"], get_file_content=True))
    
        audio_file = download_file(model_request_dict["input_args"]["file"]["file_url"])
    return audio_file

#   > QUESTION-ANSWER
def get_request_qa(model_request_dict) -> (list, list):
    _context, _question = None, None
    # Get Context
    if "context" in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['context'], list):
            _context = []
            for question in model_request_dict["input_args"]['context']:
                _context.append(download_file(question, get_file_content=True))   
    if not _context and 'file' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['file'], list):
            _context = []
            for file_idx in model_request_dict["input_args"]['file']:
                if "file_url" in file_idx:
                    _context.append(download_file(file_idx["file_url"], get_file_content=True))
    
    # Get Question
    if "question" in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['question'], list):
            _question = []
            for question in model_request_dict["input_args"]['question']:
                _question.append(download_file(question, get_file_content=True))    
    if not _question and 'text_prompt' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['text_prompt'], list):
            _question = []
            for text_prompt in model_request_dict["input_args"]['text_prompt']:
                _question.append(download_file(text_prompt, get_file_content=True))

    return _context, _question


#   > URL
def get_url_from_file(file_idx):
    file_content = download_file(file_idx, get_file_content=True)
    return get_url_from_str(file_content)

def get_request_url(model_request_dict) -> list:
    _req_url = None
    if 'url' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['url'], list):
            _req_url = []
            for curr_url in model_request_dict["input_args"]['url']:
                inst_url = get_url_from_str(curr_url)
                print("UTILS:", inst_url)
                if not inst_url:
                    inst_url = get_url_from_file(curr_url)
                if inst_url:
                    _req_url += inst_url
            
    if not _req_url and 'file' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['file'], list):
            _req_url = []
            for file_idx in model_request_dict["input_args"]['file']:
                if "file_url" in file_idx:
                    _req_url.append(download_file(file_idx["file_url"]))

    if not _req_url and 'text_prompt' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['text_prompt'], list):
            _req_url = []
            for text_prompt in model_request_dict["input_args"]['text_prompt']:
                inst_url = get_url_from_str(text_prompt)
                if not _req_url:
                    inst_url = get_url_from_file(text_prompt)
                _req_url.append(download_file(inst_url, get_file_content=True))
    return _req_url

#   > HTML
def get_html_from_str(string):
    # retrieved from https://stackoverflow.com/a/3642850 & https://stackoverflow.com/a/32680048
    pattern = re.compile(r'<html((.|[\n\r])*)\/html>')
    _res = pattern.search(string)
    if not _res:
        return None, None
    
    _html_content = f"<html{_res.group(1)}/html>"
    _tmp_html_path = os.path.join(TMP_PATH, f"tmp_html{int(time.time())}.html")
    with open(_tmp_html_path, "w") as fw:
        fw.write(_html_content)
    return _tmp_html_path, 'utf-8'

def get_html_from_file(file_idx) -> (str, str):
    _search_in_file_idx, _encoding = get_html_from_str(file_idx)
    if _search_in_file_idx:
        return _search_in_file_idx, _encoding
        
    base_filename = os.path.basename(file_idx)
    file_path = os.path.join(TMP_PATH, base_filename)
    file_tmp_path = os.path.join(TMP_PATH, "tmp_"+base_filename)
    if not file_path.endswith(".html"):
        file_path += ".html"
        file_tmp_path += ".html"
    with  requests.get(file_idx, stream=True) as req_file:
        if req_file.status_code != 200:
            return None, None
        
        if req_file.encoding is None:
            req_file.encoding = 'utf-8'

        with open(file_tmp_path, 'w') as fw:
            fw.write("")
        with open(file_tmp_path, 'a', encoding=req_file.encoding) as fa:
            for line in req_file.iter_lines(decode_unicode=True):
                if line:
                    fa.write(f"{line}\n")
                    # shutil.copyfileobj(req_file.raw, fwb)
        
        if req_file.encoding != 'utf-8':
            # inspired in https://stackoverflow.com/a/191455
            # alternative: https://superuser.com/a/1688176
            try:
                with open(file_tmp_path, 'rb') as source:
                    with open(file_path, "w") as recode:
                        recode.write(str(source.read().decode(req_file.encoding).encode("utf-8").decode("utf-8")))
                req_file.encoding = 'utf-8'
            except:
                file_path = file_tmp_path
    return file_path, req_file.encoding

def get_request_html(model_request_dict, from_url=False) -> list((str, str)):
    _req_html = None

    if not _req_html and 'html' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['html'], list):
            _req_html = []
            for html in model_request_dict["input_args"]['html']:
                _req_html.append(get_html_from_file(html))

    if not _req_html and 'file' in model_request_dict["input_args"]:
    #and "file_url" in model_request_dict["input_args"]["file"]:
        if isinstance(model_request_dict["input_args"]['file'], list):
            _req_html = []
            for file_idx in model_request_dict["input_args"]['file']:
                if "file_url" in file_idx:
                    _req_html.append(get_html_from_file(file_idx["file_url"]))

    if not _req_html and 'url' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['url'], list):
            _req_html = []
            for url in model_request_dict["input_args"]['url']:
                _req_html.append(get_html_from_file(url))

    if not _req_html and 'text_prompt' in model_request_dict["input_args"]:
        if isinstance(model_request_dict["input_args"]['text_prompt'], list):
            _req_html = []
            for text_prompt in model_request_dict["input_args"]['text_prompt']:
                _req_html.append(get_html_from_file(text_prompt))
    return _req_html