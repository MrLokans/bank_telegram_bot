* ~~add 'help' function that displays usage~~
* ~~add parsers autodiscovery (provide some common interface)~~
* ~~add some kind of memoization~~
* ~~add exchange rate display for the given date~~
* ~~show graphs with exchange rate for the given number of days~~
* ~~Add more verbose logging and logging to file~~
* ~~Turn playbook into role~~
* ~~Turn mongo installation into separate playbook~~
* ~~Cache exchange requests~~
* ~~Create local vagrant deploy~~
* ~~add '/course bank list' option to dispay banks choices: **/banks** command is used instead~~
*  Check and update Debian deployment
*  Type annotations, we use Python 3, why the hell not?
*  add **/course** bank <bank name> to see data about courses in the given bank
*  add **/compare** <currency name> see data about currency from diffrent bank
*  Setup mongodb config, create admin and normal user (dat feel when mongo's not hipster enough)
*  Rotate image cache to not overflow disk (say limit to 500 mb)
*  On big date differences dates on the plot are hardly distinctable
*  Think about inline functionality of any kind (pass exchange rates for the given currency to the chat?)
*  replace BS with lxml to speedup page parsing (or maybe use lxml as html parsing library within bs4)
*  display exchange change rates
    e.g. **/diff** <bank name> -c<currency name> -d<number of days since now> -t<type (text by default)>
*  **IMPORTANT** - add argparse or optparse to parse bot arguments instead of parsing them manually