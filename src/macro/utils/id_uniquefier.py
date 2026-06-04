from typing import Protocol


# noinspection SpellCheckingInspection
class IDUniquefier(Protocol):
    def get_id(self) -> int: ...

# noinspection SpellCheckingInspection
class DefaultIDUniquefier:
    def __init__(self):
        self.id: int = 0

    def get_id(self) -> int:
        self.id += 1
        return self.id