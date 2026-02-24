import pytest
from macro.builtin_aux_funcs import static_text_parser, args_parser, parse_value


class TestParserLogic:
    """针对宏参数解析逻辑的单元测试"""

    @pytest.mark.parametrize("text, expected", [
        ("arg1::arg2", ["arg1", "arg2"]),
        ('arg1::"quoted::arg"', ["arg1", '"quoted::arg"']),  # 引号内忽略分隔符
        (r"arg1::esc\::arg", ["arg1", "esc\\::arg"]),  # 转义分隔符处理
        ("  space  ::  args  ", ["space", "args"]),  # 自动strip
    ])
    def test_args_parser(self, text, expected):
        assert args_parser(text, "::") == expected

    @pytest.mark.parametrize("text, expected_key, expected_val", [
        ("simple_val", None, "simple_val"),
        ("key=value", "key", "value"),
        ('key="quoted=val"', "key", 'quoted=val'),  # 引号内忽略等号
        (r"key=val\=ue", "key", "val=ue"),  # 转义等号
        ("  key  =  val  ", "key", "val"),  # 等号两侧strip
    ])
    def test_parse_value(self, text, expected_key, expected_val):
        key, val = parse_value(text)
        assert key == expected_key
        assert val == expected_val

    def test_static_text_parser_complex(self):
        """测试综合解析：名字、位置参数、关键字参数"""
        text = 'my_macro::pos1::k1=v1::pos2::k2="v2::v2"'
        name, args, kwargs = static_text_parser(text, "::")

        assert name == "my_macro"
        assert args == ["pos1", "pos2"]
        assert kwargs == {"k1": "v1", "k2": 'v2::v2'}