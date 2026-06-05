from contextlib import contextmanager

from .models import (ParserConfig, CONST_ESCAPE_TAG, CONST_EQUAL_TAG, CONST_QUOTE_TAG,
                     Token, TextToken, OpenToken, CloseToken, EscapeToken, SeparatorToken, QuoteToken, EqualToken)

class Lexer:

    def __init__(self, config: ParserConfig):
        self.buffer: str = ""
        self.config: ParserConfig = config

    def feed(self, text: str) -> list[Token]:
        self.buffer += text
        return self._analyze(final=False)

    def close(self):
        return self._analyze(final=True)

    def _analyze(self, final: bool) -> list[Token]:
        i = 0
        text_buffer_start = 0

        output_buffer = []

        # flush unhandled text & escape
        @contextmanager
        def flush_op():
            nonlocal i, escape_len, text_buffer_start
            nonlocal output_buffer

            # flush text buffer:
            if i > text_buffer_start:
                output_buffer.append(
                    TextToken(
                        text=self.buffer[text_buffer_start:i]
                    )
                )

            try:
                yield

            finally:
                # followup logic:
                text_buffer_start = i

        # do lexer stuff
        while i < len(self.buffer):
            # special escape tag:
            if self.buffer.startswith(CONST_ESCAPE_TAG, i):
                with flush_op():
                    j = i
                    escape_len = 0
                    while j < len(self.buffer):
                        if self.buffer.startswith(CONST_ESCAPE_TAG, j):
                            j += len(CONST_ESCAPE_TAG)
                            escape_len += 1
                        else:
                            break
                    output_buffer.append(EscapeToken(len=escape_len, text=CONST_ESCAPE_TAG))
                    i = j
                continue

            # match full tags:
            matched = False
            for tag, token in [
                (CONST_QUOTE_TAG, QuoteToken),
                (CONST_EQUAL_TAG, EqualToken),
                (self.config.open_tag, OpenToken),
                (self.config.close_tag, CloseToken),
                (self.config.separator_tag, SeparatorToken)
            ]:
                if self.buffer.startswith(tag, i):
                    with flush_op():
                        output_buffer.append(token(text=tag))
                        i += len(tag)
                    matched = True
                    break
            if matched:
                continue

            # no full tags, check unfinished tags:
            if (
                    (not final) and
                    (
                    # unfinished open tag
                    (len(self.buffer) - i < len(self.config.open_tag)
                    and self.config.open_tag.startswith(self.buffer[i:])) or
                    # unfinished close tag
                    (len(self.buffer) - i < len(self.config.close_tag)
                    and self.config.close_tag.startswith(self.buffer[i:])) or
                    # unfinished separator tag
                    (len(self.buffer) - i < len(self.config.separator_tag)
                    and self.config.separator_tag.startswith(self.buffer[i:])))
            ):
                # leave for later
                break

            # if none of these applies, it's plain text
            else:
                i += 1

        with flush_op():
            ...

        self.buffer = self.buffer[i:]

        return output_buffer