import sys

# Token Categories
KEYWORDS = {
    "integer", "boolean", "real",
    "if", "otherwise", "fi",
    "while", "return",
    "read", "write",
    "function", "true", "false"
}

OPERATORS = {
    "==", "!=", "<=", "=>",
    "=", "+", "-", "*", "/", ">", "<"
}

SEPARATORS = {
    "(", ")", "{", "}", ";", ",", "@"
}

# Lexer Class
class Lexer:
    def __init__(self, filename):
        with open(filename, 'r') as f:
            self.source = f.read()
        self.length = len(self.source)
        self.index = 0

    def get_char(self):
        if self.index < self.length:
            ch = self.source[self.index]
            self.index += 1
            return ch
        return None

    def peek_char(self):
        if self.index < self.length:
            return self.source[self.index]
        return None

    def skip_whitespace(self):
        while self.peek_char() and self.peek_char().isspace():
            self.get_char()

    # Identifier FSM
    def identifier(self):
        lexeme = ""
        state = 0

        while True:
            ch = self.peek_char()

            if state == 0:
                if ch and ch.isalpha():
                    lexeme += self.get_char()
                    state = 1
                else:
                    return None

            elif state == 1:
                if ch and (ch.isalnum() or ch == "_"):
                    lexeme += self.get_char()
                else:
                    break

        if lexeme.lower() in KEYWORDS:
            return ("keyword", lexeme)
        else:
            return ("identifier", lexeme)

    # Integer + Real FSM
    def number(self):
        lexeme = ""
        state = 0
        is_real = False

        while True:
            ch = self.peek_char()

            if state == 0:
                if ch and ch.isdigit():
                    lexeme += self.get_char()
                    state = 1
                else:
                    return None

            elif state == 1:
                if ch and ch.isdigit():
                    lexeme += self.get_char()
                elif ch == ".":
                    is_real = True
                    lexeme += self.get_char()
                    state = 2
                else:
                    break

            elif state == 2:
                if ch and ch.isdigit():
                    lexeme += self.get_char()
                    state = 3
                else:
                    print("Lexical Error: Invalid real number")
                    return None

            elif state == 3:
                if ch and ch.isdigit():
                    lexeme += self.get_char()
                else:
                    break

        if is_real:
            return ("real", lexeme)
        else:
            return ("integer", lexeme)

    # Comment Handling
    def skip_comment(self):
        if self.peek_char() == "/" and self.source[self.index + 1] == "*":
            self.get_char()  # /
            self.get_char()  # *

            while True:
                ch = self.get_char()
                if ch is None:
                    print("Unclosed comment error")
                    return
                if ch == "*" and self.peek_char() == "/":
                    self.get_char()
                    break

    # Operators + Separators
    def operator_or_separator(self):
        ch = self.get_char()

        # Check two-character operators first
        next_ch = self.peek_char()
        if next_ch:
            combined = ch + next_ch
            if combined in OPERATORS:
                self.get_char()
                return ("operator", combined)

        if ch in OPERATORS:
            return ("operator", ch)

        if ch in SEPARATORS:
            return ("separator", ch)

        return None

    # The Main lexer() Function
    def lexer(self):
        self.skip_whitespace()

        if self.peek_char() is None:
            return None

        # Comments
        if self.peek_char() == "/" and self.source[self.index + 1] == "*":
            self.skip_comment()
            return self.lexer()

        # Identifier
        if self.peek_char().isalpha():
            return self.identifier()

        # Number
        if self.peek_char().isdigit():
            return self.number()

        # Operator or separator
        token = self.operator_or_separator()
        if token:
            return token

        # Unknown
        print("Lexical Error: Unknown character", self.get_char())
        return self.lexer()

# Main program
def main():
    if len(sys.argv) != 3:
        print("Usage: python python.py input.txt output.txt")
        return

    lexer = Lexer(sys.argv[1])

    with open(sys.argv[2], 'w') as out:
        out.write("token\t\tlexeme\n")

        while True:
            token = lexer.lexer()
            if token is None:
                break
            out.write(f"{token[0]}\t\t{token[1]}\n")

    print("Lexical analysis complete.")


if __name__ == "__main__":
    main()