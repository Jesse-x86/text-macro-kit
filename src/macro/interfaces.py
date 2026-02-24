from typing import Protocol, Callable, Optional, Awaitable, Union, ParamSpec, TypeVar, Concatenate

from pydantic import BaseModel

MacroContextType = TypeVar("MacroContextType", bound=BaseModel)
MacroStateType = TypeVar("MacroStateType", bound=BaseModel)

class MacroStateSource(Protocol[MacroStateType]):
    async def get_state(self) -> MacroStateType: ...
    async def set_state(self, state: MacroStateType) -> None: ...
    async def save_state(self) -> None: ...
P = ParamSpec("P")

# noinspection PyTypeHints
SyncMacro = Callable[Concatenate[MacroContextType, MacroStateType, P], Optional[str]]
# noinspection PyTypeHints
AsyncMacro = Callable[Concatenate[MacroContextType, MacroStateType, P], Awaitable[Optional[str]]]

Macro = Union[SyncMacro[MacroContextType, MacroStateType, P], AsyncMacro[MacroContextType, MacroStateType, P]]