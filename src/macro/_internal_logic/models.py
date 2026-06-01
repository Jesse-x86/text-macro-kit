from dataclasses import dataclass

CONST_ESCAPE_TAG: str = "\\"
CONST_QUOTE_TAG: str = "\""
CONST_EQUAL_TAG: str = "="

@dataclass(frozen=True, slots=True)
class ParserConfig:
    open_tag: str = "{{"
    close_tag: str = "}}"
    separator_tag: str = "::"

@dataclass(frozen=True, slots=True)
class Token:
    ...

@dataclass(frozen=True, slots=True)
class TextToken(Token):
    text: str

@dataclass(frozen=True, slots=True)
class EscapeToken(Token):
    len: int

@dataclass(frozen=True, slots=True)
class OpenToken(Token):
    ...

@dataclass(frozen=True, slots=True)
class CloseToken(Token):
    ...

@dataclass(frozen=True, slots=True)
class SeparatorToken(Token):
    ...


@dataclass(frozen=True, slots=True)
class QuoteToken(Token):
    ...

@dataclass(frozen=True, slots=True)
class EqualToken(Token):
    ...