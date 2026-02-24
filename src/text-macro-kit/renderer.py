import re
from contextlib import asynccontextmanager
from typing import Generic, AnyStr, Optional

from .builtin_aux_funcs import static_text_parser
from .definition_holder import MacroDefinitionHolder
from .interfaces import MacroStateSource, MacroContextType, MacroStateType, Macro

# TODO: 支持\:符号
#  支持自定义分隔符？


DEFAULT_OPEN_TAG = "{{"
DEFAULT_CLOSE_TAG = "}}"
DEFAULT_SEPARATE_TAG = "::"

# noinspection RegExpDuplicateAlternationBranch
def get_re(open_tag: str, end_tag: str) -> re.Pattern[AnyStr]:
    return re.compile(
    rf'(?P<open>{re.escape(open_tag)})|'
    rf'(?P<close>{re.escape(end_tag)})|'
    r'(?P<esc_characters>\\.)'
)


class MacroRenderer(Generic[MacroContextType, MacroStateType]):
    def __init__(
            self,
            macro_holder: MacroDefinitionHolder[MacroContextType, MacroStateType],
            state_source: MacroStateSource,
            *,
            open_tag: str = DEFAULT_OPEN_TAG,
            close_tag: str = DEFAULT_CLOSE_TAG,
            separate_tag: str = DEFAULT_SEPARATE_TAG,
    ):
        self.macro_holder = macro_holder
        self.state_source = state_source

        # 配置项
        self.open_tag = open_tag
        self.close_tag = close_tag
        self.separate_tag = separate_tag
        self.regex = get_re(self.open_tag, self.close_tag)

        # 内部状态容器 (初始化为 None)
        self._state: Optional[MacroStateType] = None
        self._context: Optional[MacroContextType] = None
        self._macros: Optional[dict[str, tuple[bool, Macro]]] = None

    # --- Properties: 提供类型安全且带检查的访问 ---

    @property
    def state(self) -> MacroStateType:
        """获取当前状态。若未在 session 内调用则抛出错误。"""
        if self._state is None:
            raise RuntimeError("Renderer state not initialized. Use 'async with renderer.session(ctx):'")
        return self._state

    @property
    def context(self) -> MacroContextType:
        """获取当前渲染上下文。"""
        if self._context is None:
            raise RuntimeError("Renderer context not initialized. Use 'async with renderer.session(ctx):'")
        return self._context

    @property
    def macros(self) -> dict[str, tuple[bool, Macro]]:
        """获取当前可用的宏定义快照。"""
        if self._macros is None:
            raise RuntimeError("Renderer macros not initialized. Use 'async with renderer.session(ctx):'")
        return self._macros

    # --- Lifecycle Management ---

    async def _save_and_clear(self):
        try:
            if self._state is not None:
                await self.state_source.set_state(self._state)
                await self.state_source.save_state()
        finally:
            self._state = None
            self._context = None
            self._macros = None

    @asynccontextmanager
    async def session(self, context: MacroContextType):
        """
        异步上下文管理器，负责渲染前的状态加载和渲染后的自动保存。
        用法:
            async with renderer.session(context):
                result = await renderer.render(text)
        """
        self._macros = self.macro_holder.get_macros()
        self._state = await self.state_source.get_state()
        self._context = context

        try:
            yield self
        finally:
            await self._save_and_clear()


    async def execute_macro(self, name: str, *args, **kwargs) -> str:
        is_async, macro = self.macros.get(name, (False, None))
        if not macro:
            raise ValueError("Invalid macro")
        result = macro(self.context, self.state, *args, **kwargs)
        if is_async:
            result = await result
        return result or ""

    async def _scan_to_stack(self, input_text: str, stack: list[list[str]]):
        last_pos = 0
        for match in self.regex.finditer(input_text):
            # 对原始文本进行遍历，尝试构建新的文本栈
            kind = match.lastgroup

            if kind == 'esc_characters':
                continue

            if kind == 'open':
                stack[-1].append(input_text[last_pos:match.start()])
                last_pos = match.end()
                stack.append([])
            elif kind == 'close':
                if len(stack) > 1:
                    stack[-1].append(input_text[last_pos:match.start()])
                    last_pos = match.end()

                    macro = "".join(stack.pop())

                    if macro.startswith("!"):
                        result = self.open_tag + macro[1:] + self.close_tag
                        stack[-1].append(result)
                    elif macro.startswith("//"):
                        result = ""
                        stack[-1].append(result)
                    else:
                        try:
                            name, args, kwargs = static_text_parser(macro, self.separate_tag)
                            result = await self.execute_macro(name, *args, **kwargs)
                            await self._scan_to_stack(result, stack)
                        except Exception as e:
                            # TODO: log error
                            result = self.open_tag + macro + self.close_tag
                            stack[-1].append(result)
        stack[-1].append(input_text[last_pos:])

    async def render(self, input_text: str) -> str:
        idx = 0
        content_list = []

        # 字符串构建栈
        # 外层：宏层级
        # 内层：宏字符串
        stack: list[list[str]] = [[]]
        await self._scan_to_stack(input_text, stack)

        fragments = ["".join(layer) for layer in stack]
        return self.open_tag.join(fragments)