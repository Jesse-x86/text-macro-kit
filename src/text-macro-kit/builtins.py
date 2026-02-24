from pydantic import BaseModel


class MacroContextBuiltin(BaseModel):
    user: str
    char: str

class MacroStateBuiltin(BaseModel):
    ...

def user(ctx: MacroContextBuiltin, state: MacroStateBuiltin):
    return ctx.user

def char(ctx: MacroContextBuiltin, state: MacroStateBuiltin):
    return ctx.char