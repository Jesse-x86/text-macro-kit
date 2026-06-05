from typing import Tuple, Optional

from .models import (ParserConfig, CONST_ESCAPE_TAG, CONST_EQUAL_TAG, CONST_QUOTE_TAG,
                     Token, TextToken, OpenToken, CloseToken, EscapeToken, SeparatorToken, QuoteToken, EqualToken,
                     DisplaySignal, TextDPSignal, EscapeDPSignal, PendingEscapeDPSignal, UpdateEscapeDPSignal,
                     MacroDPSignal, CloseMacroDPSignal, UpdateMacroDPSignal, OpenMacroDPSignal,
                     ASTObj, MacroAO, MacroRefAO, MacroArgsAO, GeneralMacroAO, SpecialMacroAO, TextAO,
                     MacroBuilder, SpecialMacroBuilder)
from ..utils.id_uniquefier import IDUniquefier
from .translator import translate


class Parser:

    def __init__(self, idu: IDUniquefier):
        self.buffer: list[MacroBuilder] = [] #unfinished AST
        self.special_buffer: list[SpecialMacroBuilder] = []
        self.pending_escape_len: int = 0
        self.idu = idu

    def feed(self, tokens: list[Token]) -> Tuple[list[DisplaySignal], list[MacroAO]]:
        i = 0
        ds_buffer: list[DisplaySignal] = []
        complete_ast_buffer: list[MacroAO] = []

        def _flush_escape() -> int:
            esc_len = self.pending_escape_len
            if self.pending_escape_len > 0:
                self.pending_escape_len = 0
            return esc_len

        def _handle_escape() -> Tuple[int, bool]:
            esc_len = self.pending_escape_len
            if self.pending_escape_len > 0:
                self.pending_escape_len = 0
                is_str = esc_len % 2 == 1
                esc_len = esc_len // 2
                ds_buffer.append(UpdateEscapeDPSignal(CONST_ESCAPE_TAG, esc_len))
                return esc_len, is_str
            return esc_len, False

        def _specialize_buffer_token(macro_type: str, raw_input: str):
            macro = self.buffer.pop()
            smb = SpecialMacroBuilder(
                macro_id=macro.macro_id,
                token_bits=macro.token_bits,
                macro_type=macro_type,
                raw_content=raw_input
            )
            self.buffer.append(smb)
            self.special_buffer.append(smb)

        while i < len(tokens):
            token = tokens[i]
            i += 1

            # get current macro
            if self.buffer:
                current_macro = self.buffer[-1]
            else:
                current_macro = None

            if self.special_buffer:
                current_special = self.special_buffer[-1]
                for sp in self.special_buffer:
                    if isinstance(token, EscapeToken):
                        sp.raw_content += token.text * token.len
                    else:
                        sp.raw_content += token.text
            else:
                current_special = None

            # \ Token
            if isinstance(token, EscapeToken):
                # special logic: record pending length
                self.pending_escape_len += token.len
                # print pending escapes
                ds_buffer.append(PendingEscapeDPSignal(CONST_ESCAPE_TAG, self.pending_escape_len))
                continue

            # = token
            if isinstance(token, EqualToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal(token.text))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    ds_buffer.append(TextDPSignal(token.text))
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(token.text)
                    current_macro.token_bits[-1].append(token)
                    continue

            # " token
            if isinstance(token, QuoteToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal(token.text))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    ds_buffer.append(TextDPSignal(token.text))
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(token.text)
                    current_macro.token_bits[-1].append(token)
                    continue

            # Text Token
            if isinstance(token, TextToken):
                esc_len = _flush_escape()
                ds_buffer.append(TextDPSignal(token.text))
                if current_macro:
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    else:
                        # is inside a macro & no escape sign in between
                        # now, if this is the beginning of a macro AND is special sign: this is special macro
                        # still in the first segment?
                        if len(current_macro.token_bits) == 1:
                            tb = current_macro.token_bits[0]
                            # no input yet?
                            if len(tb) == 0:
                                if token.text.startswith("!"):
                                    _specialize_buffer_token("!", token.text[1:])
                                    current_macro = self.buffer[-1]
                                elif token.text.startswith("//"):
                                    _specialize_buffer_token("//", token.text[2:])
                                    current_macro = self.buffer[-1]
                            # the only input is "/" and we got another "/"?
                            elif len(tb) == 1:
                                tbt = tb[0]
                                if isinstance(tbt, TextToken):
                                    if tbt.text == "/" and token.text.startswith("/"):
                                        _specialize_buffer_token("//", token.text[1:])
                                        current_macro = self.buffer[-1]
                    current_macro.token_bits[-1].append(token)
                continue

            # :: token
            if isinstance(token, SeparatorToken):
                # Not inside macro:
                if not current_macro:
                    _flush_escape()
                    ds_buffer.append(TextDPSignal(token.text))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    ds_buffer.append(TextDPSignal(token.text))
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(token.text)
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
                        current_macro.token_bits[-1].append(TextToken(token.text))
                    ds_buffer.append(TextDPSignal(token.text))
                    continue
                # if it's not a string, we'll need some bs
                else:
                    _id = self.idu.get_id()
                    ds_buffer.append(OpenMacroDPSignal(text=token.text, macro_id=_id))
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
                    ds_buffer.append(TextDPSignal(token.text))
                    continue
                # inside macro:
                else:
                    esc_len, is_str = _handle_escape()
                    if esc_len > 0:
                        current_macro.token_bits[-1].append(TextToken(CONST_ESCAPE_TAG * esc_len))
                    if is_str:
                        token = TextToken(token.text)
                        current_macro.token_bits[-1].append(token)
                        ds_buffer.append(TextDPSignal(token.text))
                    # if it's not a string, end current macro
                    else:
                        # display & label end
                        ds_buffer.append(CloseMacroDPSignal(text=token.text, macro_id=current_macro.macro_id))
                        # actual ending macro logic
                        finished_macro = self.buffer.pop()
                        # am i special?
                        if isinstance(finished_macro, SpecialMacroBuilder):
                            # are there more specials?
                            self.special_buffer.pop()
                            if self.special_buffer:
                                current_special = self.special_buffer[-1]
                            else:
                                current_special = None
                            # special parse logic:
                            macro_ast = SpecialMacroAO(
                                macro_id=finished_macro.macro_id,
                                macro_type=finished_macro.macro_type,
                                raw_content=finished_macro.raw_content[:-len(token.text)]
                            )
                        # regular macro
                        else:
                            macro_ast = translate(finished_macro)

                        # get parsed macro? if parameters illegal may get None, can handle as pure text
                        if macro_ast:
                            # if under special father hold it don't eval
                            if current_special:
                                current_special.ast_cache.append(macro_ast)
                            else:
                                complete_ast_buffer.append(macro_ast)
                    continue

        return ds_buffer, complete_ast_buffer

    def close(self) -> Tuple[list[DisplaySignal], list[MacroAO]]:
        self.buffer.clear()
        ast_buffer: list[MacroAO] = []
        for special in self.special_buffer:
            ast_buffer.extend(special.ast_cache)
        self.special_buffer.clear()
        self.pending_escape_len = 0
        return [], ast_buffer