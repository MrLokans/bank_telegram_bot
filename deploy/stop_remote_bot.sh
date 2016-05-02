ansible -i ~/servers.ini mrlokans -m service -a "name=supervisord state=stopped"
