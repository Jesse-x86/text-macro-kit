import re
from typing import ParamSpec, Callable, Concatenate, Awaitable, Optional

P = ParamSpec("P")
MacroExecutor = Callable[[Concatenate[str, P]], Awaitable[str]]


_cache_tag = None
_cache_template = None
# TODO: 换一个集中的regex管理器，集中管理缓存

text_fragment_pattern = re.compile(r'(?P<esc>\\.)|(?P<quote>")|(?P<equal>=)')

def get_re_for_args(separate_tag: str) -> re.Pattern:
    global _cache_tag, _cache_template
    if _cache_tag == separate_tag:
        # noinspection PyTypeChecker
        return _cache_template
    else:
        _cache_tag = separate_tag
        _cache_template = re.compile(
            rf'(?P<separator>{re.escape(separate_tag)})|'
            r'(?P<quote>")|'
            r'(?P<esc_characters>\\.)'
        )
        return _cache_template


def args_parser(text: str, separate_tag: str) -> list[str]:
    """
    将文本按分隔符分割。
    规则：
    1. 忽略引号内（"..."）的分隔符。
    2. 转义引号（\"）不视为引号的开始或结束。
    3. 转义分隔符（如 \::）会被视为普通字符（取决于你的业务逻辑，通常由后续处理）。
    """
    template = get_re_for_args(separate_tag)

    args = []
    last_pos = 0
    in_quote = False

    for match in template.finditer(text):
        kind = match.lastgroup
        pos = match.start()

        if kind == 'esc_characters':
            # 遇到 \. 无论是 \" 还是 \: 直接跳过，不改变 in_quote 状态
            continue

        if kind == 'quote':
            # 切换引号状态
            in_quote = not in_quote
            continue

        if kind == 'separator':
            if not in_quote:
                # 不在引号内，进行分割
                args.append(text[last_pos:pos].strip())
                last_pos = match.end()

    # 添加最后一个片段
    args.append(text[last_pos:].strip())

    return args

def parse_value(text: str) -> tuple[Optional[str], str]:
    pattern = text_fragment_pattern

    split = False
    in_quote = False
    should_lstrip = False

    last_pos = 0

    key = None
    values = []

    # 首先strip掉两边的空白，这样就只需要处理等号两侧的strip了
    text = text.strip()

    def append_segment(start, end):
        nonlocal should_lstrip
        segment = text[start:end]
        if should_lstrip:
            segment = segment.lstrip()
            should_lstrip = False
        if segment:
            values.append(segment)

    for match in pattern.finditer(text):
        kind = match.lastgroup
        start_pos = match.start()
        end_pos = match.end()

        if kind == 'esc':
            # 任务：无论是否在引号内，插入转义字符
            append_segment(last_pos, start_pos)
            values.append(text[start_pos + 1:end_pos])
            last_pos = end_pos
            continue
        elif kind == 'quote':
            # 任务：让内部的=和分隔符不识别，基本不需要特别做什么
            append_segment(last_pos, start_pos,)
            last_pos = end_pos
            in_quote = not in_quote
            continue
        elif kind == 'equal' and not in_quote and not split:
            # 只有第一个不在引号内的split需要特别处理
            split = True
            should_lstrip = True        # 需要对等号右边的第一次匹配做左侧strip
            # 对等号左侧最后一次匹配做右strip
            segment = text[last_pos:start_pos].rstrip()
            values.append(segment)
            last_pos = end_pos

            key = "".join(values)
            values=[]
            continue

    append_segment(last_pos, len(text))

    return key, "".join(values)



def static_text_parser(text: str,
                       separate_tag: str
                       ) -> tuple[str, list[str], dict[str, str]]:
    name: str = ""
    args: list[str] = []
    kwargs: dict[str, str] = {}

    separated_text = args_parser(text=text, separate_tag=separate_tag)

    if not separated_text:
        return "", [], {}

    _, name = parse_value(separated_text[0])
    if not name:
        raise ValueError("macro name should not include '='")

    for text in separated_text[1:]:
        k, v = parse_value(text)
        if not k:
            args.append(v)
        else:
            kwargs[k] = v

    return name, args, kwargs