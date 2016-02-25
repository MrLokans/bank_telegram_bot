import os

from telegram import Updater

API_ENV_NAME = 'BANK_BOT_AP_TOKEN'

api_token = os.environ.get(API_ENV_NAME, '')

if not api_token:
    raise ValueError("No API token specified.")

updater = Updater(token=api_token)

dispatcher = updater.dispatcher


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=update.message.text)


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Sorry, I didn't understand that command.")


def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.sendMessage(chat_id=update.message.chat_id, text=text_caps)


dispatcher.addTelegramCommandHandler('caps', caps)
dispatcher.addTelegramCommandHandler('start', start)
dispatcher.addTelegramCommandHandler('echo', echo)
dispatcher.addUnknownTelegramCommandHandler(unknown)
updater.start_polling()
