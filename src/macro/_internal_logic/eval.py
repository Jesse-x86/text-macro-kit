from collections import deque

from .models import *
from .. import MacroRegistry, MacroContextType


class Evaluator:

    def __init__(self, reg: MacroRegistry):
        self.reg = reg
        self.ctx = None
        self.sink = None
        self.queue: deque = deque()
        self.finished_macros: dict[int, str] = {}


    async def _eval_arg(self, arg: tuple[TextAO | MacroRefAO, ...]) -> str:
        """
        Eval a single arg
        """
        buffer = ""
        for segment in arg:
            if isinstance(segment, TextAO):
                buffer += segment.text
            elif isinstance(segment, MacroRefAO):
                # TODO: Wait if not in current dict
                result = self.finished_macros.pop(segment.macro_id, "")
                if isinstance(result, Exception):
                    raise result
                buffer += result
        return buffer

    async def _eval_args(self, args: tuple[MacroArgsAO, ...]) -> tuple[list, dict]:
        """
        Eval all args of a single macro
        """
        arg_list = []
        arg_dict = {}
        try:
            for arg in args:
                value = await self._eval_arg(arg.arg_value)
                if arg.arg_name:
                    arg_dict[arg.arg_name] = value
                else:
                    arg_list.append(value)
        except Exception as e:
            raise
        return arg_list, arg_dict

    def _set_result(self, macro_id: int, macro_result: str) -> None:
        self.finished_macros[macro_id] = macro_result
        self.sink.push(UpdateMacroDPSignal(
            macro_id=macro_id,
            text=macro_result
        ))

    def _set_exception(self, macro_id: int, macro_exception: Exception) -> None:
        ...

    async def eval(self, macro: MacroAO) -> None:
        macro_id = macro.macro_id
        if isinstance(macro, SpecialMacroAO):
            if macro.macro_type == "!":
                self._set_result(macro_id, macro.raw_content)
                return
            elif macro.macro_type == "//":
                self._set_result(macro_id, "")
                return
        elif isinstance(macro, GeneralMacroAO):
            macro_name = macro.macro
            args, kwargs = await self._eval_args(macro.args)
            # execute & return

            macro_is_async, macro_func = self.reg.get_macros().get(macro_name, (None, None))
            if not macro_func:
                return



        ...

    def set_ctx(self, ctx: MacroContextType):
        self.ctx = ctx

    def set_sink(self, sink):
        self.sink = sink

    async def feed(self, macro: MacroAO) -> None:
        self.queue.append(macro)

    async def close(self) -> None:
        # TODO: Wait until all execution complete
        self.ctx = None
        self.sink = None