from typing import Optional

from .models import (Token, TextToken, QuoteToken, EqualToken,
                     MacroAO, MacroRefAO, MacroArgsAO, GeneralMacroAO, MacroBuilder, TextAO)

def is_nonempty(text: str):
    return text and text.strip()

def _strip_tokens(arg: list[Token | MacroRefAO]) -> list[TextAO | MacroRefAO]:
    new_list = []
    # remove front empty
    lo = 0
    while lo < len(arg):
        # None-text token cannot be empty
        if not isinstance(arg[lo], TextToken):
            break

        # if after strip is not empty, is not empty.
        if is_nonempty(arg[lo].text):
            break
        lo += 1

    # remove end empty
    hi = len(arg) - 1
    while lo <= hi:
        # None-text token cannot be empty
        if not isinstance(arg[hi], TextToken):
            break

        # if after strip is not empty, is not empty.
        if is_nonempty(arg[hi].text):
            break
        hi -= 1

    if hi < lo:
        return []

    # remove quotes
    if hi > lo and isinstance(arg[hi], QuoteToken) and isinstance(arg[lo], QuoteToken):
        new_list = arg[lo+1: hi]
    else:
        new_list = arg[lo: hi+1]
        if lo == hi:
            if isinstance(new_list[0], TextToken):
                new_list[0] = TextToken(new_list[0].text.strip())
        else:
            if isinstance(new_list[0], TextToken):
                new_list[0] = TextToken(new_list[0].text.lstrip())
            if isinstance(new_list[-1], TextToken):
                new_list[-1] = TextToken(new_list[-1].text.rstrip())

    # text-fy
    str_buffer = ""
    ret_list = []
    for token in new_list:
        if isinstance(token, MacroRefAO):
            if str_buffer:
                ret_list.append(TextAO(str_buffer))
                str_buffer = ""
            ret_list.append(token)
        else:
            str_buffer += token.text

    if str_buffer:
        ret_list.append(TextAO(str_buffer))
    return ret_list

def _parse_name(arg: list[Token | MacroRefAO]) -> Optional[str]:
    name = ""
    arg = _strip_tokens(arg)
    for token in arg:
        if isinstance(token, MacroRefAO):
            return None
        name += token.text
    return name

def _parse_arg(arg: list[Token | MacroRefAO]) -> MacroArgsAO:
    # find if any equal token exists
    i = 0
    while i < len(arg):
        if isinstance(arg[i], EqualToken):
            break
        i += 1
    # if exist eq token:
    name = None
    if i < len(arg):
        name = _parse_name(arg[:i])
    # name is reasonable, rest is arg
    if name:
        arg = _strip_tokens(arg[i+1:])
    # name not reasonable or no eq token present, whole is arg
    else:
        arg = _strip_tokens(arg)
    return MacroArgsAO(arg_name=name, arg_value=tuple(arg))

def translate(builder: MacroBuilder) -> Optional[MacroAO]:
    macro_id = builder.macro_id
    tb = builder.token_bits
    # parse macro name
    macro_name = ""
    # there should be at least a name
    if len(tb) > 0:
        # if the segment is not empty, parse it
        macro_name = _parse_name(tb[0])
        # found illegal case, no macro built
        if macro_name is None:
            return None

        # elsewise macro name is set
        # even if empty, no operation needed
        # leave only args to handle
        tb = tb[1:]

    args = [_parse_arg(arg) for arg in tb]

    # Empty macro:
    return GeneralMacroAO(macro_id=macro_id, macro=macro_name, args=tuple(args))