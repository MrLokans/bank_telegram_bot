* ~~add 'help' function that displays usage~~
*  add '/course bank list' option to dispay banks choices
*  add /course bank <bank name> to see data about courses in the given bank
*  add /compare <currency name> see data about currency from diffrent bank
*  add parsers autodiscovery (provide some common interface)
* ~~add some kind of memoization~~
*  display exchange change rates
    e.g. /diff <bank name> -c<currency name> -d<number of days since now> -t<type (text by default)>
* ~~add exchange rate display for the given date~~
* ~~show graphs with exchange rate for the given number of days~~
*  replace BS with lxml to speedup page parsing
* ~~Add more verbose logging and logging to file~~
*  Rotate image cache to not overflow disk (say limit to 500 mb)
*  On big date differences date on the plot are hardly distinctable
* ~~Turn playbook into role~~
* ~~Turn mongo installation into separate playbook~~
* ~~Cache exchange requests~~
*  Setup mongodb config, create admin and normal user
* ~~Create local vagrant deploy~~
*  Check and update Debian deployment