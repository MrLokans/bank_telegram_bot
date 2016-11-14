VENVDIR=./venv
REQUIREMENTS_FILE=./deploy/roles/telegrambot/files/debian_requirements.txt

test:
	python -m unittest discover -s ./bot

deploy:
	ansible-playbook -i ~/servers.ini ./deploy/deploy.yml

stop:
	/bin/bash ./deploy/stop_remote_bot.sh

restart:
	/bin/bash ./deploy/restart_remote_bot.sh
