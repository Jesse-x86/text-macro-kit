import pytest
from pydantic import BaseModel
from macro.registry import MacroRegistry
from macro.renderer import MacroRenderer


# --- 准备工作 ---

class MockContext(BaseModel):
    pass


class MockState(BaseModel):
    pass


class SimpleStateSource:
    async def get_state(self): return MockState()

    async def set_state(self, s): pass

    async def save_state(self): pass


@pytest.fixture
def renderer():
    registry = MacroRegistry[MockContext, MockState]()
    # 注册一些用于工具的宏
    registry.register(lambda ctx, state, x: f"({x})", func_name="wrap")
    registry.register(lambda ctx, state, a, b: f"{a}+{b}", func_name="add")
    registry.register(lambda ctx, state, **kw: str(kw.get('val', '')), func_name="get_kw")

    return MacroRenderer(registry, SimpleStateSource())


# --- 核心测试用例 ---

@pytest.mark.asyncio
class TestAdvancedRendering:

    async def test_quote_consumption(self, renderer):
        """测试主人提到的引号消耗逻辑：引号被吃掉，转义引号保留"""
        async with renderer.session(MockContext()):
            # 情况1：正常引号包裹，参数应该拿到内部值（不含引号）
            # 注意：这里需要宏里能返回原始参数，我们临时注册一个
            renderer.macros["echo"] = (False, lambda c, s, x: x)

            # 这里的输入是 echo::"hello"
            # args_parser 会识别引号并把 hello 提出来
            res1 = await renderer.render('{{echo::"hello"}}')
            assert res1 == "hello"  # 引号被消耗了

            # 情况2：转义引号应该被保留（根据 parse_value 逻辑）
            res2 = await renderer.render(r'{{echo::\"stay\"}}')
            assert res2 == '"stay"'

    async def test_deep_recursion(self, renderer):
        """测试深度嵌套宏渲染"""
        async with renderer.session(MockContext()):
            # {{wrap::{{wrap::{{wrap::deep}}}}}} -> (((deep)))
            text = "{{wrap::{{wrap::{{wrap::deep}}}}}}"
            result = await renderer.render(text)
            assert result == "(((deep)))"

    async def test_complex_mixed_args(self, renderer):
        """测试位置参数和关键字参数混用，且包含嵌套"""
        async with renderer.session(MockContext()):
            # {{add::{{wrap::1}}::b={{wrap::2}}}}
            # 预期：wrap(1) + wrap(2) -> (1)+(2)
            text = "{{add::{{wrap::1}}::b={{wrap::2}}}}"
            result = await renderer.render(text)
            assert result == "(1)+(2)"

    async def test_error_recovery(self, renderer):
        """测试宏执行失败时的降级逻辑（返回原始文本）"""

        def broken_macro(ctx, state):
            raise RuntimeError("Boom!")

        renderer.registry.register(broken_macro, func_name="boom")

        async with renderer.session(MockContext()):
            # 当执行 boom 抛出异常时，渲染器应该捕捉它并返回原始文本
            text = "Pre-{{boom}}-Post"
            result = await renderer.render(text)
            assert result == "Pre-{{boom}}-Post"

    async def test_unclosed_tags(self, renderer):
        """测试未闭合标签的处理"""
        async with renderer.session(MockContext()):
            # 只有开没有关，应该被当做普通文本
            text = "Hello {{wrap::incomplete"
            result = await renderer.render(text)
            assert result == "Hello {{wrap::incomplete"

    async def test_escaped_open_tag(self, renderer):
        """测试转义开符号 \{ """
        async with renderer.session(MockContext()):
            # 根据代码逻辑，\{ 会被匹配为 esc_characters 而跳过
            # 如果 last_pos 处理正确，它应该原样留在文本里
            text = r"Normal \{{wrap::test\}}"
            result = await renderer.render(text)
            # 预期渲染器不会识别这个宏，因为它被转义了
            # 结果应该保留原始字符串（取决于主人对反斜杠的处理偏好）
            assert "{{wrap::test}}" not in result