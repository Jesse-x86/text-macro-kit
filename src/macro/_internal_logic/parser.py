from typing import Tuple

from .models import (ParserConfig, CONST_ESCAPE_TAG, CONST_EQUAL_TAG, CONST_QUOTE_TAG,
                     Token, TextToken, OpenToken, CloseToken, EscapeToken, SeparatorToken, QuoteToken, EqualToken,
                     DisplaySignal, TextDPSignal, EscapeDPSignal, PendingEscapeDPSignal, UpdateEscapeDPSignal,
                     MacroDPSignal, MacroFinDPSignal, MacroRawDPSignal, MacroStartDPSignal,
                     ASTObj, MacroAO, MacroRefAO, MacroArgsAO, GeneralMacroAO, SpecialMacroAO, TextAO,
                     MacroBuilder, MacroArgBuilder, GeneralMacroBuilder, SpecialMacroBuilder, UndecidedMacroBuilder)
from ..utils.id_uniquefier import IDUniquefier


class Parser:

    def __init__(self, config: ParserConfig, idu: IDUniquefier):
        self.buffer: list[MacroBuilder] = [] #unfinished AST
        self.pending_escape_len: int = 0
        self.config: ParserConfig = config
        self.idu = idu

    def feed(self, tokens: list[Token]) -> Tuple[list[DisplaySignal], list[ASTObj]]:
        i = 0
        ds_buffer: list[DisplaySignal] = []
        complete_ast_buffer: list[ASTObj] = []

        in_quote = False

        def _flush_escape():
            if self.pending_escape_len > 0:
                self.pending_escape_len = 0

        def _handle_escape() -> bool:
            if self.pending_escape_len > 0:
                is_str = self.pending_escape_len % 2 == 1
                var = self.pending_escape_len // 2
                self.pending_escape_len = 0
                ds_buffer.append(UpdateEscapeDPSignal(CONST_ESCAPE_TAG, var))
                return is_str
            return False

        while i < len(tokens):
            token = tokens[i]
            i += 1

            # Escape Token: No special case
            if isinstance(token, EscapeToken):
                self.pending_escape_len += token.len
                ds_buffer.append(PendingEscapeDPSignal(CONST_ESCAPE_TAG, self.pending_escape_len))
                continue

            # get current macro
            if self.buffer:
                current_macro = self.buffer[-1]
            else:
                current_macro = None

            # = token
            if isinstance(token, EqualToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal("="))
                    continue
                # inside a macro
                else:
                    # is special macro?
                    if isinstance(current_macro, SpecialMacroBuilder):
                        current_macro.raw_content += "="
                        continue
                    # is undecided?
                    if isinstance(current_macro, UndecidedMacroBuilder):
                        # decide: it's regular macro
                        self.buffer.pop()
                        current_macro = GeneralMacroBuilder()
                        self.buffer.append(current_macro)
                        # move on, no continue
                    # in macro name part?
                    if not current_macro.args:
                        current_macro.macro_name += "="
                        continue
                    # in arg part
                    arg = current_macro.args[-1]
                    # first eq?
                    if arg.arg_value


                    ...

            # Text Token
            if isinstance(token, TextToken):
                # Not inside macro:
                if not current_macro:
                    ds_buffer.append(TextDPSignal(token.text))
                    continue
                # Inside macro:
                else:
                    ...


            # :: token
            if isinstance(token, SeparatorToken):
                if not current_macro:
                    ds_buffer.append(TextDPSignal(self.config.separator_tag))
                    continue
                else:
                    _id = current_macro.macro_id
                    ds_buffer.append(MacroRawDPSignal(macro_id=_id, text=self.config.separator_tag))


            # {{ token
            if isinstance(token, OpenToken):
                _id = self.idu.get_id()

                # if already in a macro chain
                if isinstance(current_macro, GeneralMacroBuilder):
                    #
                    current_macro.args[-1].arg_value.append(MacroRefAO(_id))

                i += 1
                next_token = self.buffer[i]
                self.buffer.append()

        return ds_buffer, complete_ast_buffer

    def close(self) -> None:
        self.buffer.clear()
        self.pending_escape_len = 0
        return