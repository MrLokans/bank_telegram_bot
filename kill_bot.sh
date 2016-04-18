#!/bin/bash

bot_pid=$(ps aux | grep 'python bot.py$' | cut -d' ' -f2)

if [ -z $bot_pid ]
then
	echo "Bot process is not found!"	
else
	kill -9 $bot_pid
fi

