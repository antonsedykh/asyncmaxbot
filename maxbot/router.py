from typing import Any, Dict

class Router:
    def __init__(self) -> None:
        self.message_handlers = []
        self.callback_query_handlers = []
        self.bot_started_handlers = []
        self.user_added_handlers = []
        self.chat_member_updated_handlers = []
        # Другие типы обработчиков будут добавлены по мере необходимости

    def message_handler(self, *filters):
        def decorator(handler):
            self.message_handlers.append({"handler": handler, "filters": filters})
            return handler
        return decorator

    def callback_query_handler(self, *filters):
        def decorator(handler):
            self.callback_query_handlers.append({"handler": handler, "filters": filters})
            return handler
        return decorator

    def bot_started_handler(self, *filters):
        def decorator(handler):
            self.bot_started_handlers.append({"handler": handler, "filters": filters})
            return handler
        return decorator

    def user_added_handler(self, *filters):
        def decorator(handler):
            self.user_added_handlers.append({"handler": handler, "filters": filters})
            return handler
        return decorator

    def chat_member_updated_handler(self, *filters):
        def decorator(handler):
            self.chat_member_updated_handlers.append({"handler": handler, "filters": filters})
            return handler
        return decorator 