import os

from bot.telegrambot import (
    create_bot,
    settings
)

api_token = os.environ.get(settings.API_ENV_NAME, '')

if not api_token:
    raise ValueError("No API token specified.")

if __name__ == '__main__':
    updater = create_bot(api_token)
    updater.start_polling()
    updater.idle()
