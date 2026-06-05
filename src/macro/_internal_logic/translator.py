from typing import Optional

from .models import (Token, TextToken, QuoteToken, EqualToken,
                     MacroAO, MacroRefAO, MacroArgsAO, GeneralMacroAO, MacroBuilder, TextAO)


def _strip_tokens(arg: list[Token | MacroRefAO]) -> list[TextAO | MacroRefAO]:
    new_list = []
    # remove front empty
    i = 0
    cut_l_quote = False
    cut_r_quote = False
    while i < len(arg):
        # None-text token cannot be empty
        if not isinstance(arg[i], TextToken):
            if isinstance(arg[i], QuoteToken):
                cut_l_quote = True
            break
        # only strip left side
        var = arg[i].text.lstrip()
        i += 1

        # if after strip is not empty, is not empty.
        if not len(var) == 0:
            new_list.append(TextToken(var))
            break

    # remove end empty
    j = len(arg) - 1
    while i < j:
        # None-text token cannot be empty
        if not isinstance(arg[j], TextToken):
            if isinstance(arg[j], QuoteToken):
                cut_r_quote = True
            new_list.extend(arg[i:j+1])
            break
        # only strip left side
        var = arg[j].text.rstrip()
        j -= 1

        # if after strip is not empty, is not empty.
        if not len(var) == 0:
            new_list.extend(arg[i:j+1])
            new_list.append(TextToken(var))
            break

    if len(new_list) == 1 and isinstance(new_list[0], TextToken):
        new_list[0] = TextToken(new_list[0].text.rstrip())

    # remove quotes
    if len(new_list) > 1 and cut_l_quote and cut_r_quote:
        new_list = new_list[1:-1]

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

        # elsewise macro name is empty, no operation needed
        # leave only args to handle
        tb = tb[1:]

    args = [_parse_arg(arg) for arg in tb]

    # Empty macro:
    return GeneralMacroAO(macro_id=macro_id, macro=macro_name, args=tuple(args))