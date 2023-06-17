#!/bin/sh
weston_user=$(ps aux | grep '/usr/bin/weston '|grep -v 'grep'|awk '{print $1}')
source /usr/local/Vin/config_board.sh
cmd="python3 /usr/local/Vin/camera.py --framerate $DFPS --frame_width $DWIDTH --frame_height $DHEIGHT $COMPUTE_ENGINE"
if [ "$weston_user" != "root" ]; then
	echo "user : "$weston_user
	script -qc "su -l $weston_user -c '$cmd'"
else
	$cmd
fi
