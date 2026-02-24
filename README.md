# 📦 Text-Macro-Kit (macro)

这是一个优雅、轻量且强大的 Python 文本宏处理工具包。它支持异步宏、深度嵌套、复杂的参数解析以及类型安全的状态管理。


### 📦 来源与关联

`text-macro-kit` 最初是作为 [**TavernKit**](https://github.com/Jesse-x86/TavernKit) 项目的核心组件开发的。

因为 TavernKit 仍在开发中，而我看到了宏的潜力，为了让更多开发者能享受到灵活宏渲染的便利，我决定将其作为一个独立的模块先行发布。

如果你正在寻找一个开箱即用的酒馆式上下文管理方案，囊括了从“自动根据token长度截断聊天记录”到“不仅仅是插入 `system prompt` 而是可以塞到任何地方的世界书”等等功能，那么敬请期待 **TavernKit**（正在开发中，完工后将开放仓库！）。

### 🔮 进阶功能预告

在未来的 **TavernKit** 中，你将获得超越基础工具包的“完全体”宏体验：
- **深度集成**：与聊天记录管理自动关联，不再需要自己实现 `MacroStateSource`，我们将提供完善的持久化管理器。
- **标准流程**: 宏渲染将作为 prompt 渲染的一个环节，被放在整个渲染引擎的标准流程中。开发者只需要调用渲染引擎的 `render` 函数即可。
- **标准宏库**：内置一套针对角色扮演和文本生成的常用宏定义，囊括了{{user}}、{{char}}这类最常用的宏和{{getvar::arg}}、{{setvar::arg::value}}这类复杂宏。


## 🌟 特性

- **类型安全**：基于 Pydantic 定义上下文（Context）和状态（State）。
- **异步支持**：完美支持 `async/await` 宏函数。
- **复杂语法**：支持位置参数、关键字参数以及宏的深度嵌套。
- **生命周期管理**：通过 `session` 自动处理状态的加载与持久化。

## 🚀 快速开始

### 1. 定义模型与状态源

首先，你需要定义你的上下文和状态模型，并实现一个状态加载器。

```python
from pydantic import BaseModel
from macro.interfaces import MacroStateSource

# 1. 定义数据模型
class MyContext(BaseModel):
    user_name: str

class MyState(BaseModel):
    gold: int = 100

# 2. 实现状态源 (例如从数据库或内存读取)
class MemoryStateSource:
    def __init__(self):
        self.state = MyState()
    
    async def get_state(self) -> MyState:
        return self.state

    async def set_state(self, state: MyState):
        self.state = state

    async def save_state(self):
        print("状态已保存到数据库喵！")
```

### 2. 注册宏函数

创建一个注册表并将你的函数注册进去。

```python
from macro.registry import MacroRegistry

registry = MacroRegistry[MyContext, MyState]()

@registry.register
def greet(ctx: MyContext, state: MyState):
    return f"你好，{ctx.user_name}！"

@registry.register
async def add_gold(ctx: MyContext, state: MyState, amount: str):
    state.gold += int(amount)
    return f"获得了 {amount} 金币，当前：{state.gold}"
```

### 3. 渲染文本

实例化渲染器并在 `session` 中执行渲染。

```python
import asyncio
from macro.renderer import MacroRenderer

async def main():
    state_source = MemoryStateSource()
    renderer = MacroRenderer(registry, state_source)
    
    context = MyContext(user_name="主人")
    
    # 使用 session 管理生命周期
    async with renderer.session(context):
        text = "欢迎回来！{{greet}} 目前状态：{{add_gold::50}}"
        result = await renderer.render(text)
        print(result) 
        # 输出: 欢迎回来！你好，主人！ 目前状态：获得了 50 金币，当前：150

asyncio.run(main())
```

## 📝 语法指南

| 语法 | 说明 | 示例 |
| :--- | :--- | :--- |
| `{{name}}` | 执行基础宏 | `{{greet}}` |
| `{{name::arg1::k=v}}` | 带参数的宏 | `{{shop::apple::count=5}}` |
| `{{!name}}` | 字面量（不执行） | 解析为 `{{name}}` |
| `{{//comment}}` | 注释（渲染后消失） | `{{// 这里是备注}}` |
| `{{a::{{b}}}}` | 嵌套宏 | 先执行 `b`，结果作为 `a` 的参数 |
| `\{{text\}}` | 转义符号 | 解析为原始的 `{{` 和 `}}` |
