from dataclasses import dataclass, field
from typing import Optional, Literal

# --- GeneralConfig ---

CONST_ESCAPE_TAG: str = "\\"
CONST_QUOTE_TAG: str = "\""
CONST_EQUAL_TAG: str = "="

@dataclass(frozen=True, slots=True)
class ParserConfig:
    open_tag: str = "{{"
    close_tag: str = "}}"
    separator_tag: str = "::"

# --- Tokens ---

@dataclass(frozen=True, slots=True)
class Token:
    text: str

@dataclass(frozen=True, slots=True)
class TextToken(Token):
    ...

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

# --- DPSignal ---

@dataclass(frozen=True, slots=True)
class DisplaySignal:
    text: str # Content to display

@dataclass(frozen=True, slots=True)
class TextDPSignal(DisplaySignal):
    ...

@dataclass(frozen=True, slots=True)
class EscapeDPSignal(DisplaySignal):
    len: int

@dataclass(frozen=True, slots=True)
class PendingEscapeDPSignal(EscapeDPSignal):
    ...

@dataclass(frozen=True, slots=True)
class UpdateEscapeDPSignal(EscapeDPSignal):
    ...

@dataclass(frozen=True, slots=True)
class MacroDPSignal(DisplaySignal):
    macro_id: int # ID of the macro to manipulate

@dataclass(frozen=True, slots=True)
class OpenMacroDPSignal(MacroDPSignal):
    ...

@dataclass(frozen=True, slots=True)
class CloseMacroDPSignal(MacroDPSignal):
    ...

@dataclass(frozen=True, slots=True)
class UpdateMacroDPSignal(MacroDPSignal):
    ...

# --- AST ---

@dataclass(frozen=True, slots=True)
class ASTObj:
    ...

@dataclass(frozen=True, slots=True)
class TextAO(ASTObj):
    text: str

@dataclass(frozen=True, slots=True)
class MacroAO(ASTObj):
    macro_id: int

@dataclass(frozen=True, slots=True)
class MacroRefAO(MacroAO):
    ...

@dataclass(frozen=True, slots=True)
class MacroArgsAO:
    arg_name: Optional[str]
    arg_value: tuple[TextAO | MacroRefAO, ...]

@dataclass(frozen=True, slots=True)
class SpecialMacroAO(MacroAO):
    macro_type: str
    raw_content: str

@dataclass(frozen=True, slots=True)
class GeneralMacroAO(MacroAO):
    macro: str
    args: tuple[MacroArgsAO, ...]

# --- Token -> AST ---
@dataclass(slots=True)
class MacroBuilder:
    macro_id: int
    token_bits: list[list[Token | MacroRefAO]]

@dataclass(slots=True)
class SpecialMacroBuilder(MacroBuilder):
    macro_type: str
    raw_content: str
    ast_cache: list[MacroAO] = field(default_factory=list)