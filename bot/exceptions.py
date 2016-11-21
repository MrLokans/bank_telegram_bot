class BotArgumentParsingError(Exception):
    pass


class BotLoggedError(Exception):
    """When this exception is raised its message is sent back to user"""
