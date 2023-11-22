#!/bin/bash

# GET USER PATH
get_user=$(who)
USER=${get_user%% *}
USER_HOME="/home/$USER"
STATUS_FLAG_PATH="$USER_HOME/Desota/DeRunner/status.txt"


# -- Edit bellow vvvv DeSOTA DEVELOPER EXAMPLe: miniconda + pip pckgs + systemctl service

# SERVICE VARS
SERV_NAME=derunner.service
SERV_WAITER=""
SHAKE_RES=""



# -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

# SUPER USER RIGHTS
[ "$UID" -eq 0 ] || { 
    echo "This script must be run as root."; 
    echo "  sudo $0";
    exit 1;
}

# IPUT ARGS - -s="Start Model Service"; -d="Print stuff and Pause at end"
systemctl_flag=0
while getopts fn: flag
do
    case $flag in
        f) systemctl_flag=1;;
    esac
done

echo "Inform Main"
echo "0">$STATUS_FLAG_PATH
chown $USER $STATUS_FLAG_PATH

if [ "$systemctl_flag" -eq "1" ]; then
    exit 0
fi

echo "Starting Service..."
echo "    service name: $SERV_NAME"

systemctl start $SERV_NAME
start_res=$? 
if test "$SERV_WAITER" = ""
then
    echo "    $SERV_NAME started"
    exit $start_res
fi

_curr_stat=$($SERV_WAITER 2>/dev/nul)
_char_stat=1
sp="/-\|"
echo
echo -n "Wainting for asset handshake  ";
while [ "$_curr_stat" != "$SHAKE_RES" ];
do
    printf "\b${sp:_char_stat++%${#sp}:1}"
    _curr_stat=$($SERV_WAITER 2>/dev/nul)
done
echo
echo "    $SERV_NAME started"
exit 0