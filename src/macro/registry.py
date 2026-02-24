import inspect
from typing import Optional, Generic

from .interfaces import Macro, MacroContextType, MacroStateType


class MacroRegistry(Generic[MacroContextType, MacroStateType]):
    def __init__(self):
        self.macros: dict[str, tuple[bool, Macro[MacroContextType, MacroStateType, ...]]] = {}

    def register(self, macro: Macro[MacroContextType, MacroStateType, ...], *, func_name: Optional[str] = None):
        if not func_name:
            func_name = macro.__name__
        is_async = inspect.iscoroutinefunction(macro)
        self.macros[func_name] = (is_async, macro)

    def get_macros(self) -> dict[str, tuple[bool, Macro[MacroContextType, MacroStateType, ...]]]:
        return dict(self.macros)