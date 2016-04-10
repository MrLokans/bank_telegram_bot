bot_pid=$(ps aux | grep 'python bot.py$' | cut -d' ' -f2)
kill -9 $bot_pid
