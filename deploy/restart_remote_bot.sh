ansible -i ~/servers.ini mrlokans -m supervisorctl -a "name=bot_project:telegram_bot state=restarted"