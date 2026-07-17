"""Text-Macro-Kit —— SillyTavern 风格、有状态、异步的文本宏渲染库。

这个文件是**对外公开 API 的唯一门面**:用户 `import macro` 后只应碰到这里 re-export 的符号。
真正的解析实现(lexer / parser / eval)全在 `macro._internal_logic` 里 —— 前导下划线表示
"私有、不保证稳定、随时可重构",外部不要直接 import 它。

公开面只有三层,且都刻意保持稳定(内部逻辑大修时这三层的签名不应跟着变):
  - interfaces:用户要实现 / 用来标注类型的协议与类型别名
  - registry  :注册宏的容器
  - renderer  :驱动渲染的入口
"""

# --- 渲染入口与默认标签 ---
from .renderer import (
    MacroRenderer,
    DEFAULT_OPEN_TAG,
    DEFAULT_CLOSE_TAG,
    DEFAULT_SEPARATE_TAG,
)

# --- 宏注册表 ---
from .registry import MacroRegistry

# --- 协议 / 类型别名(用户实现 state source、标注宏签名时用) ---
from .interfaces import (
    MacroStateSource,   # 用户实现:状态的 get/set/save
    Macro,              # 宏的类型别名(同步或异步)
    SyncMacro,
    AsyncMacro,
    MacroContextType,   # 泛型参数:供 MacroRegistry[Ctx, State] 等标注用
    MacroStateType,
)

# 显式声明公开面;`from macro import *` 与静态检查都以此为准。
# 不在此列的(尤其 _internal_logic 下的一切)均视为内部实现。
__all__ = [
    # renderer
    "MacroRenderer",
    "DEFAULT_OPEN_TAG",
    "DEFAULT_CLOSE_TAG",
    "DEFAULT_SEPARATE_TAG",
    # registry
    "MacroRegistry",
    # interfaces
    "MacroStateSource",
    "Macro",
    "SyncMacro",
    "AsyncMacro",
    "MacroContextType",
    "MacroStateType",
]
from .interfaces import (
    MacroStateType,
    MacroContextType,
    MacroStateSource,
    SyncMacro,
    AsyncMacro,
    Macro
)

from .registry import MacroRegistry
from .renderer import MacroRenderer

__all__ = [
    "MacroStateSource",
    "Macro",
    "SyncMacro",
    "AsyncMacro",
    "MacroContextType",
    "MacroStateType",
    "MacroRenderer",
    "MacroRegistry",
]