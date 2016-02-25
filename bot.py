# TODO:
#  [ ] add 'help' function that displays usage
#  [ ] add '/course bank list' option to dispay banks choices
#  [ ] add /course bank <bank name> to see data about courses in the given bank
#  [ ] add /compare <currency name> see data about currency from diffrent bank
#  [ ] add parsers autodiscovery (provide some common interface)

import os

from telegram import Updater

from bank_parsers import BelgazpromParser

API_ENV_NAME = 'BANK_BOT_AP_TOKEN'

api_token = os.environ.get(API_ENV_NAME, '')

if not api_token:
    raise ValueError("No API token specified.")

updater = Updater(token=api_token)

dispatcher = updater.dispatcher


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="I'm a bot, please talk to me!")


def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=update.message.text)


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Sorry, I didn't understand that command.")


def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.sendMessage(chat_id=update.message.chat_id, text=text_caps)


def course(bot, update, args):
    if not args:
        belgazrprom = BelgazpromParser()
        all_currencies = belgazrprom.currencies
        displayed_values = ['{}: {} {}'.format(x.iso, x.sell, x.buy)
                            for x in all_currencies]

        currencies_text_value = "\n".join(displayed_values)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Currencies: \n{}".format(currencies_text_value))
        return
    if len(args) == 1:
        belgazrprom = BelgazpromParser()
        cur = belgazrprom.get_currency(currency_name=args[0])
        if cur.name == 'NoValue':
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Unknown currency: {}".format(args[0]))
        else:
            text = "{}: {} {}".format(cur.iso, cur.sell, cur.buy)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=text)


dispatcher.addTelegramCommandHandler('caps', caps)
dispatcher.addTelegramCommandHandler('start', start)
dispatcher.addTelegramCommandHandler('echo', echo)
dispatcher.addTelegramCommandHandler('course', course)
dispatcher.addUnknownTelegramCommandHandler(unknown)
updater.start_polling()
