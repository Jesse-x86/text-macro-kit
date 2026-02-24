import pytest
import asyncio
from typing import Any
from pydantic import BaseModel

from macro.registry import MacroRegistry


# 定义用于测试的上下文和状态模型（符合 Protocol 要求）
class MockContext(BaseModel):
    pass


class MockState(BaseModel):
    value: str = ""


# --- 测试用宏函数 ---

def sync_macro_func(ctx: MockContext, state: MockState) -> str:
    """一个标准的同步宏测试函数"""
    return "sync_result"


async def async_macro_func(ctx: MockContext, state: MockState) -> str:
    """一个标准的异步宏测试函数"""
    await asyncio.sleep(0)
    return "async_result"


# --- 单元测试用例 ---

class TestMacroRegistry:

    def test_initial_registry_is_empty(self):
        """测试注册表初始化时应该是空的"""
        registry = MacroRegistry[MockContext, MockState]()
        assert registry.get_macros() == {}

    def test_register_sync_macro(self):
        """测试注册同步宏及其元数据识别"""
        registry = MacroRegistry[MockContext, MockState]()
        registry.register(sync_macro_func)

        macros = registry.get_macros()
        assert "sync_macro_func" in macros
        is_async, func = macros["sync_macro_func"]

        assert is_async is False
        assert func == sync_macro_func
        assert func(MockContext(), MockState()) == "sync_result"

    @pytest.mark.asyncio
    async def test_register_async_macro(self):
        """测试注册异步宏及其元数据识别"""
        registry = MacroRegistry[MockContext, MockState]()
        registry.register(async_macro_func)

        macros = registry.get_macros()
        assert "async_macro_func" in macros
        is_async, func = macros["async_macro_func"]

        assert is_async is True
        assert func == async_macro_func
        # 验证确实可以异步执行
        result = await func(MockContext(), MockState())
        assert result == "async_result"

    def test_register_with_custom_name(self):
        """测试使用自定义名称注册宏"""
        registry = MacroRegistry[MockContext, MockState]()
        custom_name = "my_custom_macro"
        registry.register(sync_macro_func, func_name=custom_name)

        macros = registry.get_macros()
        assert custom_name in macros
        assert "sync_macro_func" not in macros
        assert macros[custom_name][1] == sync_macro_func

    def test_get_macros_returns_defensive_copy(self):
        """测试 get_macros 返回的是字典副本，防止外部意外修改"""
        registry = MacroRegistry[MockContext, MockState]()
        registry.register(sync_macro_func)

        macros = registry.get_macros()
        # 尝试篡改返回的字典
        macros["malicious_key"] = (False, sync_macro_func)

        # 验证原始注册表未受影响
        assert "malicious_key" not in registry.get_macros()
        assert len(registry.get_macros()) == 1

    def test_overwrite_registration(self):
        """测试重复注册同名宏时，后者应该覆盖前者"""
        registry = MacroRegistry[MockContext, MockState]()

        def new_macro(ctx, state): return "new"

        registry.register(sync_macro_func, func_name="same_name")
        registry.register(new_macro, func_name="same_name")

        macros = registry.get_macros()
        assert macros["same_name"][1] == new_macro