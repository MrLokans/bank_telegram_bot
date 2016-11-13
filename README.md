Description
===========

Telegram bot scraping actual currency exchange rates of different banks in Minsk.

Screenshots
-----------
![Bot's screenshot](docs/screen.png?raw=true "CourseBot")


Currently supported banks
-------------------------
- NBRB
- BGP
- Belgaprombank
- Priorbank

Available commands
------------------
- ```/help``` - shows bot's help
- ```/course -d <days_ago> -c <currency_code>``` - display exchange rates for the currently selected bank
для указанной валюты или длявсех валют.
- ```/graph -d <days_ago> -c <currency_code>``` - plot exchange rates for the given number of days
- ```/banks``` - list of supported banks.
- ```/set <bank_name>``` - set default bank for all of the operations
- ```/best -c <currency_code> -d <days_ago>``` - best exchange rates
