#!/bin/bash

# GET USER PATH
get_user=$(who)
USER=${get_user%% *}
USER_HOME="/home/$USER"
STATUS_FLAG_PATH="$USER_HOME/Desota/DeRunner/status.txt"

# -- Edit bellow vvvv DeSOTA DEVELOPER EXAMPLe: miniconda + pip pckgs + systemctl service

# SERVICE VARS
SERV_NAME=derunner.service



# -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

# SUPER USER RIGHTS
[ "$UID" -eq 0 ] || { 
    echo "This script must be run as root."; 
    echo "  sudo $0";
    exit 1;
}

echo "Inform Main"
echo "1">$STATUS_FLAG_PATH
chown $USER $STATUS_FLAG_PATH

echo "Stoping Service..."
echo "    service name: $SERV_NAME"


systemctl --no-block stop $SERV_NAME

echo "    $SERV_NAME stopped"
exit
