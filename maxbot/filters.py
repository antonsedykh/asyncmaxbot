"""
Фильтры для обработки сообщений
"""

from abc import ABC, abstractmethod
from typing import Callable, Union, List, Any, Optional, Pattern
import re
from loguru import logger
from .max_types import Context

class BaseFilter(ABC):
    """Абстрактный базовый класс для всех фильтров."""
    
    @abstractmethod
    async def check(self, ctx: Context) -> bool:
        """
        Метод, который должен быть реализован в каждом фильтре.

        :param ctx: Контекст обновления для проверки.
        :return: bool - прошел ли фильтр проверку.
        """
        pass

class CommandFilter(BaseFilter):
    """Фильтр для текстовых команд, например, /start."""
    
    def __init__(self, commands: Union[str, List[str]]):
        """
        :param commands: Команда или список команд (без '/').
        """
        if isinstance(commands, str):
            commands = [commands]
        self.commands = [cmd.lower() for cmd in commands]
    
    async def check(self, ctx: Context) -> bool:
        if not ctx.text:
            return False
        
        text = ctx.text.lower().strip()
        if not text.startswith('/'):
            return False
        
        command = text.split()[0][1:]  # Убираем '/'
        return command in self.commands

class TextFilter(BaseFilter):
    """Фильтр по тексту сообщения."""
    
    def __init__(self, texts: Union[str, List[str]], exact: bool = True, ignore_case: bool = False):
        """
        :param texts: Текст или список текстов для проверки.
        :param exact: Если True, ищет точное совпадение. Если False - частичное.
        :param ignore_case: Если True, игнорирует регистр.
        """
        if isinstance(texts, str):
            texts = [texts]
        self.texts = texts
        self.exact = exact
        self.ignore_case = ignore_case
    
    async def check(self, ctx: Context) -> bool:
        if not ctx.text:
            return False
        
        text_to_check = ctx.text.lower() if self.ignore_case else ctx.text
        patterns = [p.lower() if self.ignore_case else p for p in self.texts]
        if self.exact:
            return text_to_check in patterns
        else:
            return any(t in text_to_check for t in patterns)

class RegexFilter(BaseFilter):
    """Фильтр по регулярному выражению."""
    
    def __init__(self, pattern: str, flags: int = 0):
        """
        :param pattern: Строка с регулярным выражением.
        :param flags: Флаги для re.compile.
        """
        self.pattern = re.compile(pattern, flags)
    
    async def check(self, ctx: Context) -> bool:
        if not ctx.text:
            return False
        return bool(self.pattern.search(ctx.text))

class AttachmentTypeFilter(BaseFilter):
    """Фильтр по типу вложения (image, video, audio, file, sticker)."""
    def __init__(self, types: Union[str, List[str]]):
        """
        :param types: Тип или список типов вложений.
        """
        if isinstance(types, str):
            types = [types]
        self.types = set(types)
    async def check(self, ctx: Context) -> bool:
        if not ctx.attachments:
            return False
        return any(getattr(att, 'type', None) in self.types for att in ctx.attachments)

class HasAttachmentFilter(BaseFilter):
    """Фильтр, проверяющий наличие любого вложения в сообщении."""
    def __init__(self, has: bool = True):
        """
        :param has: Если True, проверяет наличие. Если False - отсутствие.
        """
        self.has = has
    
    async def check(self, ctx: Context) -> bool:
        return bool(ctx.attachments) == self.has

# --- Удобные функции для создания фильтров ---

def command(commands: Union[str, List[str]]) -> CommandFilter:
    """Фабричная функция для создания `CommandFilter`."""
    return CommandFilter(commands)

def text(texts: Union[str, List[str]], exact: bool = True, ignore_case: bool = False) -> TextFilter:
    """Фабричная функция для создания `TextFilter`."""
    return TextFilter(texts, exact, ignore_case)

def regex(pattern: str, flags: int = 0) -> RegexFilter:
    """Фабричная функция для создания `RegexFilter`."""
    return RegexFilter(pattern, flags)

def attachment_type(types: Union[str, List[str]]) -> AttachmentTypeFilter:
    """Фабричная функция для создания `AttachmentTypeFilter`."""
    return AttachmentTypeFilter(types)

def has_attachment(has: bool = True) -> "HasAttachmentFilter":
    """Фабричная функция для создания `HasAttachmentFilter`."""
    return HasAttachmentFilter(has)

# --- Алиасы для импорта ---
Command = CommandFilter
Text = TextFilter
Regex = RegexFilter
Attachment = AttachmentTypeFilter
HasAttachment = HasAttachmentFilter  # Алиас для совместимости

# Алиасы для совместимости с aiogram-style
State = None  # Пока не реализовано состояние

# --- Комбинированные фильтры ---

class AndFilter(BaseFilter):
    """Фильтр, который проходит только если ВСЕ дочерние фильтры прошли."""
    
    def __init__(self, *filters: BaseFilter):
        """
        :param filters: Список фильтров для объединения через AND.
        """
        self.filters = filters
    
    async def check(self, ctx: Context) -> bool:
        results = [await f.check(ctx) for f in self.filters]
        return all(results)

class OrFilter(BaseFilter):
    """Фильтр, который проходит если ХОТЯ БЫ ОДИН дочерний фильтр прошел."""
    
    def __init__(self, *filters: BaseFilter):
        """
        :param filters: Список фильтров для объединения через OR.
        """
        self.filters = filters
    
    async def check(self, ctx: Context) -> bool:
        results = [await f.check(ctx) for f in self.filters]
        return any(results)

class NotFilter(BaseFilter):
    """Фильтр, который инвертирует результат другого фильтра."""
    
    def __init__(self, filter_obj: BaseFilter):
        """
        :param filter_obj: Фильтр для инвертирования.
        """
        self.filter_obj = filter_obj
    
    async def check(self, ctx: Context) -> bool:
        return not await self.filter_obj.check(ctx)

# --- Новые фильтры ---

class TimeFilter(BaseFilter):
    """Фильтр по времени суток."""
    
    def __init__(self, start_hour: int = 0, end_hour: int = 23):
        """
        :param start_hour: Начальный час (0-23).
        :param end_hour: Конечный час (0-23).
        """
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    async def check(self, ctx: Context) -> bool:
        import datetime
        current_hour = datetime.datetime.now().hour
        
        if self.start_hour <= self.end_hour:
            return self.start_hour <= current_hour <= self.end_hour
        else:
            # Для случаев типа "с 22:00 до 06:00"
            return current_hour >= self.start_hour or current_hour <= self.end_hour

class UserFilter(BaseFilter):
    """Фильтр по ID пользователя."""
    
    def __init__(self, user_ids: Union[int, List[int]]):
        """
        :param user_ids: ID пользователя или список ID.
        """
        if isinstance(user_ids, int):
            user_ids = [user_ids]
        self.user_ids = set(user_ids)
    
    async def check(self, ctx: Context) -> bool:
        return ctx.user_id in self.user_ids

class CustomFilter(BaseFilter):
    """Кастомный фильтр на основе функции."""
    
    def __init__(self, func: Callable[[Context], bool]):
        """
        :param func: Функция, принимающая Context и возвращающая bool.
        """
        self.func = func
    
    async def check(self, ctx: Context) -> bool:
        return self.func(ctx)

# --- Фабричные функции для комбинированных фильтров ---

def and_filter(*filters: BaseFilter) -> AndFilter:
    """Фабричная функция для создания `AndFilter`."""
    return AndFilter(*filters)

def or_filter(*filters: BaseFilter) -> OrFilter:
    """Фабричная функция для создания `OrFilter`."""
    return OrFilter(*filters)

def not_filter(filter_obj: BaseFilter) -> NotFilter:
    """Фабричная функция для создания `NotFilter`."""
    return NotFilter(filter_obj)

def time_filter(start_hour: int = 0, end_hour: int = 23) -> TimeFilter:
    """Фабричная функция для создания `TimeFilter`."""
    return TimeFilter(start_hour, end_hour)

def user_filter(user_ids: Union[int, List[int]]) -> UserFilter:
    """Фабричная функция для создания `UserFilter`."""
    return UserFilter(user_ids)

def custom_filter(func: Callable[[Context], bool]) -> CustomFilter:
    """Фабричная функция для создания `CustomFilter`."""
    return CustomFilter(func)

# --- Операторы для фильтров ---

def __and__(self, other):
    """Оператор & для объединения фильтров через AND."""
    return AndFilter(self, other)

def __or__(self, other):
    """Оператор | для объединения фильтров через OR."""
    return OrFilter(self, other)

def __invert__(self):
    """Оператор ~ для инвертирования фильтра."""
    return NotFilter(self)

# Добавляем операторы к базовому классу
BaseFilter.__and__ = __and__
BaseFilter.__or__ = __or__
BaseFilter.__invert__ = __invert__

# --- MagicFilter система ---

class MagicFilter:
    """
    Гибкая система фильтрации для создания сложных условий.
    
    Позволяет писать фильтры в стиле:
    F.text.contains("привет")
    F.user.id == 123
    F.command == "start"
    """
    
    def __init__(self):
        self._conditions = []
    
    def __getattr__(self, name):
        """Создает атрибут для фильтрации"""
        return MagicAttribute(name)
    
    def __getitem__(self, key):
        """Поддержка индексации F['text']"""
        return MagicAttribute(key)
    
    def __eq__(self, other):
        """Поддержка F.text == 'value'"""
        return MagicCondition(self, '==', other)
    
    def __ne__(self, other):
        """Поддержка F.text != 'value'"""
        return MagicCondition(self, '!=', other)
    
    def __lt__(self, other):
        """Поддержка F.user.id < 100"""
        return MagicCondition(self, '<', other)
    
    def __le__(self, other):
        """Поддержка F.user.id <= 100"""
        return MagicCondition(self, '<=', other)
    
    def __gt__(self, other):
        """Поддержка F.user.id > 100"""
        return MagicCondition(self, '>', other)
    
    def __ge__(self, other):
        """Поддержка F.user.id >= 100"""
        return MagicCondition(self, '>=', other)
    
    def contains(self, value):
        """Поддержка F.text.contains('hello')"""
        return MagicCondition(self, 'contains', value)
    
    def startswith(self, value):
        """Поддержка F.text.startswith('/')"""
        return MagicCondition(self, 'startswith', value)
    
    def endswith(self, value):
        """Поддержка F.text.endswith('!')"""
        return MagicCondition(self, 'endswith', value)
    
    def in_(self, values):
        """Поддержка F.user.id.in_([1, 2, 3])"""
        return MagicCondition(self, 'in', values)
    
    def __and__(self, other):
        """Поддержка F.text & F.user.id == 123"""
        return AndFilter(self, other)
    
    def __or__(self, other):
        """Поддержка F.text | F.user.id == 123"""
        return OrFilter(self, other)
    
    def __invert__(self):
        """Поддержка ~F.text"""
        return NotFilter(self)

class MagicAttribute:
    """Атрибут для MagicFilter"""
    
    def __init__(self, name):
        self.name = name
    
    def __eq__(self, other):
        return MagicCondition(self, '==', other)
    
    def __ne__(self, other):
        return MagicCondition(self, '!=', other)
    
    def __lt__(self, other):
        return MagicCondition(self, '<', other)
    
    def __le__(self, other):
        return MagicCondition(self, '<=', other)
    
    def __gt__(self, other):
        return MagicCondition(self, '>', other)
    
    def __ge__(self, other):
        return MagicCondition(self, '>=', other)
    
    def contains(self, value):
        return MagicCondition(self, 'contains', value)
    
    def startswith(self, value):
        return MagicCondition(self, 'startswith', value)
    
    def endswith(self, value):
        return MagicCondition(self, 'endswith', value)
    
    def in_(self, values):
        return MagicCondition(self, 'in', values)

class MagicCondition(BaseFilter):
    """Условие для MagicFilter"""
    
    def __init__(self, attribute, operator, value):
        self.attribute = attribute
        self.operator = operator
        self.value = value
    
    async def check(self, ctx: Context) -> bool:
        """Проверяет условие для контекста"""
        try:
            # Получаем значение атрибута из контекста
            actual_value = self._get_attribute_value(ctx, self.attribute.name)
            
            # Применяем оператор
            return self._apply_operator(actual_value, self.operator, self.value)
        except Exception as e:
            logger.debug(f"Error in MagicCondition: {e}")
            return False
    
    def _get_attribute_value(self, ctx: Context, attr_name: str):
        """Получает значение атрибута из контекста"""
        if attr_name == 'text':
            return ctx.text
        elif attr_name == 'command':
            if ctx.text and ctx.text.startswith('/'):
                return ctx.text.split()[0][1:].lower()
            return None
        elif attr_name == 'user':
            return ctx.user
        elif attr_name == 'chat':
            return ctx.chat
        elif attr_name == 'attachment':
            return ctx.attachments
        elif attr_name == 'has_attachments':
            return ctx.has_attachments
        elif attr_name == 'user_id':
            return ctx.user_id
        elif attr_name == 'chat_id':
            return ctx.chat_id
        elif attr_name == 'message_id':
            return ctx.message_id
        elif attr_name == 'from_user':
            return ctx.from_user
        elif attr_name == 'date':
            return ctx.date
        elif attr_name == 'forward_from':
            return ctx.forward_from
        elif attr_name == 'reply_to_message':
            return ctx.reply_to_message
        else:
            # Попытка получить атрибут через getattr
            return getattr(ctx, attr_name, None)
    
    def _apply_operator(self, actual_value, operator, expected_value):
        """Применяет оператор сравнения"""
        if actual_value is None:
            return False
        
        if operator == '==':
            return actual_value == expected_value
        elif operator == '!=':
            return actual_value != expected_value
        elif operator == '<':
            return actual_value < expected_value
        elif operator == '<=':
            return actual_value <= expected_value
        elif operator == '>':
            return actual_value > expected_value
        elif operator == '>=':
            return actual_value >= expected_value
        elif operator == 'contains':
            if isinstance(actual_value, str) and isinstance(expected_value, str):
                return expected_value.lower() in actual_value.lower()
            return False
        elif operator == 'startswith':
            if isinstance(actual_value, str) and isinstance(expected_value, str):
                return actual_value.lower().startswith(expected_value.lower())
            return False
        elif operator == 'endswith':
            if isinstance(actual_value, str) and isinstance(expected_value, str):
                return actual_value.lower().endswith(expected_value.lower())
            return False
        elif operator == 'in':
            if isinstance(expected_value, (list, tuple, set)):
                return actual_value in expected_value
            return False
        else:
            return False

# Создаем глобальный экземпляр MagicFilter
F = MagicFilter()

# Алиасы для удобства
Magic = MagicFilter
Filter = MagicFilter 