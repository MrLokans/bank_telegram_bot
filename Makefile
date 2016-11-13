VENVDIR=./venv
REQUIREMENTS_FILE=./deploy/roles/telegrambot/files/debian_requirements.txt

test:
	python -m unittest discover -s ./bot