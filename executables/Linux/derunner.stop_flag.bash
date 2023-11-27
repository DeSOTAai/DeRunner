#!/bin/bash

# GET USER PATH
get_user=$(who)
USER=${get_user%% *}
USER_HOME="/home/$USER"
STATUS_FLAG_PATH="$USER_HOME/Desota/DeRunner/status.txt"

# SERVICE VARS
SERV_NAME=derunner.service

# SUPER USER RIGHTS
[ "$UID" -eq 0 ] || { 
    echo "This script must be run as root."; 
    echo "  sudo $0";
    exit 1;
}

# IPUT ARGS - -s="Start Model Service"; -d="Print stuff and Pause at end"
echo "Inform Main"
echo "1">$STATUS_FLAG_PATH
chown $USER $STATUS_FLAG_PATH

while : ; 
do 
    systemctl is-active --quiet $SERV_NAME
    if [ $? -ne 0 ]; then
        exit 0
    fi
done
