import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-uh", "--user_home", 
    help="Specify User PATH to handle with admin requests",
    type=str)
args = parser.parse_args()


USER_PATH=None
if args.user_home:
    if os.path.isdir(args.user_home):
        USER_PATH = args.user_home
if not USER_PATH:
    USER_PATH = os.path.expanduser('~')



# -- Edit bellow vvvv DeSOTA DEVELOPER EXAMPLe: miniconda + pip pckgs + systemctl service

CURR_PATH = os.path.dirname(os.path.realpath(__file__))

TARGET_RUN_FILE = os.path.join(CURR_PATH, "derunner.service.bash")
TARGET_SERV_FILE = os.path.join(CURR_PATH, "derunner.service")

MODEL_PATH=os.path.join(USER_PATH, "Desota", "DeRunner")
MODEL_ENV=os.path.join(MODEL_PATH, "env")
SERV_DESC="Desota/DeRunner - Main Runner of Desota Services"
SERV_PORT=8880
SERV_RUN_CMD=f"/bin/bash {TARGET_RUN_FILE}"
PYTHON_MAIN_CMD=f"{MODEL_ENV}/bin/python3 {MODEL_PATH}/DeRunner.py"



# -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

# SERVICE RUNNER
TEMPLATE_SERVICE_RUNNER=f'''#!/bin/bash
# GET USER PATH
while true
do
    {PYTHON_MAIN_CMD}
done
# Inform Crawl Finish
echo Service as Terminated !'''

with open(TARGET_RUN_FILE, "w") as fw:
    fw.write(TEMPLATE_SERVICE_RUNNER)

# SERVICE FILE
TEMPLATE_SERVICE=f'''[Unit]
Description={SERV_DESC}
After=network.target
StartLimitIntervalSec=0
StartLimitBurst=5
StartLimitAction=reboot.

[Service]
Type=simple
Restart=always
RestartSec=2
ExecStart={SERV_RUN_CMD}

[Install]
WantedBy=multi-user.target'''

with open(TARGET_SERV_FILE, "w") as fw:
    fw.write(TEMPLATE_SERVICE)
    
    
USER=USER_PATH.split("/")[-1]
os.system(f"chown -R {USER} {TARGET_RUN_FILE}")
os.system(f"chown -R {USER} {TARGET_SERV_FILE}")
exit(0)