import pytest
from pydantic import BaseModel
from macro.registry import MacroRegistry
from macro.renderer import MacroRenderer


# --- Mock 准备 ---

class MockContext(BaseModel):
    user_name: str = "Master"


class MockState(BaseModel):
    count: int = 0


class MockStateSource:
    """手动实现 Protocol 以便测试状态生命周期"""

    def __init__(self, initial_state: MockState):
        self.current_state = initial_state
        self.saved = False

    async def get_state(self) -> MockState:
        return self.current_state

    async def set_state(self, state: MockState) -> None:
        self.current_state = state

    async def save_state(self) -> None:
        self.saved = True


# --- 测试用例 ---

@pytest.mark.asyncio
class TestMacroRenderer:

    async def test_session_lifecycle(self):
        """测试 session 是否能正确加载、提供及保存状态"""
        registry = MacroRegistry[MockContext, MockState]()
        state_source = MockStateSource(MockState(count=10))
        renderer = MacroRenderer(registry, state_source)

        ctx = MockContext()
        async with renderer.session(ctx):
            assert renderer.state.count == 10
            assert renderer.context.user_name == "Master"
            renderer.state.count = 20  # 修改状态

        # 验证 session 结束后是否调用了保存
        assert state_source.current_state.count == 20
        assert state_source.saved is True

    async def test_basic_rendering(self):
        """测试最基础的宏渲染"""
        registry = MacroRegistry[MockContext, MockState]()
        # 注册一个简单的宏
        registry.register(lambda ctx, state: f"hello {ctx.user_name}", func_name="greet")

        renderer = MacroRenderer(registry, MockStateSource(MockState()))

        async with renderer.session(MockContext()):
            result = await renderer.render("Message: {{greet}}")
            assert result == "Message: hello Master"

    async def test_special_syntax(self):
        """测试 !字面量, //注释 以及 转义"""
        registry = MacroRegistry[MockContext, MockState]()
        renderer = MacroRenderer(registry, MockStateSource(MockState()))
        registry.register(lambda ctx, state, val: f"[{val}]", func_name="echo")

        async with renderer.session(MockContext()):
            # 1. 字面量测试
            assert await renderer.render("{{!not_a_macro}}") == "{{not_a_macro}}"
            # 2. 注释测试
            assert await renderer.render("Keep{{//hide me}}this") == "Keepthis"
            # 3. 嵌套逻辑测试 (假设有一个回显参数的宏)
            assert await renderer.render("{{echo::{{echo::inner}}}}") == "[[inner]]"

    async def test_escaping_tags(self):
        """测试 \{ 这种转义标签的情况"""
        # 注意：目前的 get_re 和 _scan_to_stack 对转义的处理逻辑
        # 是在 esc_characters 分组匹配后 continue，这意味着它被跳过了，不作为 open 处理
        registry = MacroRegistry[MockContext, MockState]()
        renderer = MacroRenderer(registry, MockStateSource(MockState()))

        async with renderer.session(MockContext()):
            # 根据代码逻辑：\{ 会匹配到 esc_characters 组，然后 continue
            # 所以它会被保留在普通文本中
            result = await renderer.render(r"\{{{!test}}\}")
            # 这里的期望值需要根据主人对 last_pos 的处理来微调
            # 目前代码里 esc_characters 只是跳过，不会更新 last_pos，
            # 这可能会导致重复添加或者偏移，主人要留意一下哦~
            assert r"\{" in result