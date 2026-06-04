from typing import Tuple, Optional

from .models import (ParserConfig, CONST_ESCAPE_TAG, CONST_EQUAL_TAG, CONST_QUOTE_TAG,
                     Token, TextToken, OpenToken, CloseToken, EscapeToken, SeparatorToken, QuoteToken, EqualToken,
                     DisplaySignal, TextDPSignal, EscapeDPSignal, PendingEscapeDPSignal, UpdateEscapeDPSignal,
                     MacroDPSignal, CloseMacroDPSignal, UpdateMacroDPSignal, OpenMacroDPSignal,
                     ASTObj, MacroAO, MacroRefAO, MacroArgsAO, GeneralMacroAO, SpecialMacroAO, TextAO,
                     MacroBuilder)
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

        def _flush_escape() -> int:
            esc_len = self.pending_escape_len
            if self.pending_escape_len > 0:
                self.pending_escape_len = 0
            return esc_len

        def _handle_escape() -> (int, bool):
            esc_len = self.pending_escape_len
            if self.pending_escape_len > 0:
                self.pending_escape_len = 0
                is_str = esc_len % 2 == 1
                esc_len = esc_len // 2
                ds_buffer.append(UpdateEscapeDPSignal(CONST_ESCAPE_TAG, esc_len))
                return esc_len, is_str
            return esc_len, False

        while i < len(tokens):
            token = tokens[i]
            i += 1

            # get current macro
            if self.buffer:
                current_macro = self.buffer[-1]
            else:
                current_macro = None

            # \ Token
            if isinstance(token, EscapeToken):
                # special logic:
                self.pending_escape_len += token.len
                ds_buffer.append(PendingEscapeDPSignal(CONST_ESCAPE_TAG, self.pending_escape_len))
                continue

            # = token
            if isinstance(token, EqualToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal(CONST_EQUAL_TAG))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    ds_buffer.append(TextDPSignal(CONST_EQUAL_TAG))
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(CONST_EQUAL_TAG)
                    current_macro.token_bits[-1].append(token)
                    continue

            # " token
            if isinstance(token, QuoteToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal(CONST_QUOTE_TAG))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    ds_buffer.append(TextDPSignal(CONST_QUOTE_TAG))
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(CONST_QUOTE_TAG)
                    current_macro.token_bits[-1].append(token)
                    continue

            # Text Token
            if isinstance(token, TextToken):
                esc_len = _flush_escape()
                ds_buffer.append(TextDPSignal(token.text))
                if current_macro:
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    current_macro.token_bits[-1].append(token)
                continue

            # :: token
            if isinstance(token, SeparatorToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal(self.config.separator_tag))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    ds_buffer.append(TextDPSignal(self.config.separator_tag))
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(self.config.separator_tag)
                        current_macro.token_bits[-1].append(token)
                    # if it's not a string, build a new segment
                    else:
                        current_macro.token_bits.append([])
                    continue

            # {{ token
            if isinstance(token, OpenToken):
                # Must handle escape first
                esc_len, is_str = _handle_escape()

                if current_macro and esc_len > 0:
                    current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                # if it's a string, then no special handle needed
                if is_str:
                    if current_macro:
                        current_macro.token_bits[-1].append(TextToken(self.config.open_tag))
                    ds_buffer.append(TextDPSignal(self.config.open_tag))
                    continue
                # if it's not a string, we'll need some bs
                else:
                    _id = self.idu.get_id()
                    ds_buffer.append(OpenMacroDPSignal(text=self.config.open_tag, macro_id=_id))
                    if current_macro:
                        ref = MacroRefAO(_id)
                        current_macro.token_bits[-1].append(ref)
                    new_macro = MacroBuilder(macro_id=_id, token_bits=[[]])
                    self.buffer.append(new_macro)
                    continue

            # }} token
            if isinstance(token, CloseToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal(self.config.close_tag))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(self.config.close_tag)
                        current_macro.token_bits[-1].append(token)
                        ds_buffer.append(TextDPSignal(self.config.close_tag))
                    # if it's not a string, end current macro
                    else:
                        # display & label end
                        ds_buffer.append(CloseMacroDPSignal(text=self.config.close_tag, macro_id=current_macro.macro_id))
                        self.buffer.pop()
                        macro_ast = self._parse(current_macro)
                        if macro_ast:
                            complete_ast_buffer.append(macro_ast)
                    continue

        return ds_buffer, complete_ast_buffer

    def close(self) -> None:
        self.buffer.clear()
        self.pending_escape_len = 0
        return

    def _parse(self, builder: MacroBuilder) -> Optional[ASTObj]:
        ...