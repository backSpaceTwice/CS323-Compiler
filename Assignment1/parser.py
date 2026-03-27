"""
Rat26S Syntax Analyzer — recursive descent parser (LL(1)-style).

Standalone Assignment1 version.
Uses lexer from this folder (python.py: lexer(content)).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import List, Optional, Tuple

_LEXER_PATH = Path(__file__).resolve().parent / "python.py"
_spec = importlib.util.spec_from_file_location("rat26s_lexer", _LEXER_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load lexer from {_LEXER_PATH}")
_lexer_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lexer_mod)
lexer = _lexer_mod.lexer

# Lines that are not token traces are indented so Token: lines stand out.
_OUTPUT_INDENT = "  "

TokenRow = Tuple[str, str, int]


class ParseError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class Parser:
    REL_OPS = ("==", "!=", "<=", "=>", "<", ">")

    def __init__(self, tokens: List[TokenRow], out) -> None:
        self.tokens = tokens
        self._i = 0
        self.out = out
        self.print_switch = True
        self.current_token: Optional[str] = None
        self.current_lexeme: str = ""
        self.current_line: int = 1

    def _token_display(self, tok: str) -> str:
        return tok[:1].upper() + tok[1:] if tok else "EOF"

    def _prod(self, text: str) -> None:
        if self.print_switch:
            self.out.write(_OUTPUT_INDENT + text + "\n")

    def _advance(self) -> None:
        if self._i >= len(self.tokens):
            self.current_token = None
            self.current_lexeme = ""
            return
        row = self.tokens[self._i]
        self._i += 1
        if len(row) >= 3:
            self.current_token, self.current_lexeme, self.current_line = row[0], row[1], row[2]
        else:
            self.current_token, self.current_lexeme = row[0], row[1]
            self.current_line = 1
        if self.current_token == "invalid":
            self._syntax_error("valid token", f"invalid character {self.current_lexeme!r}")
        self.out.write(f"Token: {self._token_display(self.current_token)} Lexeme: {self.current_lexeme}\n")

    def peek(self) -> Optional[Tuple[str, str]]:
        if self._i >= len(self.tokens):
            return None
        row = self.tokens[self._i]
        return (row[0], row[1])

    def _syntax_error(self, expected: str, got_detail: Optional[str] = None) -> None:
        line = self.current_line
        tok = self.current_token if self.current_token is not None else "EOF"
        lex = self.current_lexeme if self.current_token is not None else ""
        detail = got_detail if got_detail is not None else f"{tok} / {lex!r}"
        msg = f"Syntax Error at line {line}: Expected {expected} but got {detail}"
        self.out.write(_OUTPUT_INDENT + msg + "\n")
        raise ParseError(msg)

    def match_token(self, expected_type: str) -> None:
        if self.current_token != expected_type:
            self._syntax_error(expected_type, f"{self.current_token} / {self.current_lexeme!r}")
        self._advance()

    def match_keyword(self, word: str) -> None:
        if self.current_token != "keyword" or self.current_lexeme != word:
            self._syntax_error(f"keyword '{word}'", f"{self.current_token} / {self.current_lexeme!r}")
        self._advance()

    def match_operator(self, op: str) -> None:
        if self.current_token != "operator" or self.current_lexeme != op:
            self._syntax_error(f"operator '{op}'", f"{self.current_token} / {self.current_lexeme!r}")
        self._advance()

    def match_separator(self, sep: str) -> None:
        if self.current_token != "separator" or self.current_lexeme != sep:
            self._syntax_error(f"separator '{sep}'", f"{self.current_token} / {self.current_lexeme!r}")
        self._advance()

    def match_eof(self) -> None:
        if self.current_token is not None:
            self._syntax_error("end of input", f"{self.current_token} / {self.current_lexeme!r}")

    def Rat26S(self) -> None:
        self._prod("<Rat26S> -> <StatementList>")
        self.StatementList()
        self.match_eof()

    def StatementList(self) -> None:
        if self.current_token is None:
            self._prod("<StatementList> -> ε")
            return
        if self.current_token == "separator" and self.current_lexeme == "}":
            self._prod("<StatementList> -> ε")
            return
        self._prod("<StatementList> -> <Statement> <StatementList>")
        self.Statement()
        self.StatementList()

    def Statement(self) -> None:
        if self.current_token is None:
            self._syntax_error("statement", "EOF")
        if self.current_token == "keyword":
            kw = self.current_lexeme
            if kw == "if":
                self._prod("<Statement> -> <If>")
                self.If()
            elif kw == "while":
                self._prod("<Statement> -> <While>")
                self.While()
            elif kw == "return":
                self._prod("<Statement> -> <Return>")
                self.Return()
            elif kw == "write":
                self._prod("<Statement> -> <Print>")
                self.Print()
            elif kw == "read":
                self._prod("<Statement> -> <Scan>")
                self.Scan()
            elif kw == "function":
                self._prod("<Statement> -> <FunctionDef>")
                self.FunctionDef()
            elif kw in ("integer", "boolean", "real"):
                self._prod("<Statement> -> <Declaration>")
                self.Declaration()
            else:
                self._syntax_error("statement (if, while, return, write, read, function, or type)", f"keyword '{kw}'")
        elif self.current_token == "separator" and self.current_lexeme == "{":
            self._prod("<Statement> -> <CompoundStatement>")
            self.CompoundStatement()
        elif self.current_token == "identifier":
            nxt = self.peek()
            if nxt and nxt[0] == "operator" and nxt[1] == "=":
                self._prod("<Statement> -> <Assign>")
                self.Assign()
            elif nxt and nxt[0] == "separator" and nxt[1] == "(":
                self._prod("<Statement> -> <CallStatement>")
                self.CallStatement()
            else:
                self._syntax_error("'=' or '(' after identifier", repr(nxt))
        else:
            self._syntax_error("statement", f"{self.current_token} / {self.current_lexeme!r}")

    def FunctionDef(self) -> None:
        self._prod("<FunctionDef> -> function <Identifier> ( <ParameterList> ) <CompoundStatement>")
        self.match_keyword("function")
        self.match_token("identifier")
        self.match_separator("(")
        self.ParameterList()
        self.match_separator(")")
        self.CompoundStatement()

    def ParameterList(self) -> None:
        if self.current_token == "separator" and self.current_lexeme == ")":
            self._prod("<ParameterList> -> ε")
            return
        self._prod("<ParameterList> -> identifier <ParameterListPrime>")
        self.match_token("identifier")
        self.ParameterListPrime()

    def ParameterListPrime(self) -> None:
        if self.current_token == "separator" and self.current_lexeme == ",":
            self._prod("<ParameterListPrime> -> , identifier <ParameterListPrime>")
            self.match_separator(",")
            self.match_token("identifier")
            self.ParameterListPrime()
        else:
            self._prod("<ParameterListPrime> -> ε")

    def Declaration(self) -> None:
        self._prod("<Declaration> -> <Qualifier> identifier <OptInit> ;")
        self.Qualifier()
        self.match_token("identifier")
        self.OptInit()
        self.match_separator(";")

    def Qualifier(self) -> None:
        if self.current_token != "keyword" or self.current_lexeme not in ("integer", "boolean", "real"):
            self._syntax_error("integer, boolean, or real", f"{self.current_token} / {self.current_lexeme!r}")
        self._prod(f"<Qualifier> -> {self.current_lexeme}")
        self.match_keyword(self.current_lexeme)

    def OptInit(self) -> None:
        if self.current_token == "operator" and self.current_lexeme == "=":
            self._prod("<OptInit> -> = <Expression>")
            self.match_operator("=")
            self.Expression()
        else:
            self._prod("<OptInit> -> ε")

    def CompoundStatement(self) -> None:
        self._prod("<CompoundStatement> -> { <StatementList> }")
        self.match_separator("{")
        self.StatementList()
        self.match_separator("}")

    def If(self) -> None:
        self._prod("<If> -> if ( <Condition> ) <CompoundStatement> <OptOtherwise>")
        self.match_keyword("if")
        self.match_separator("(")
        self.Condition()
        self.match_separator(")")
        self.CompoundStatement()
        self.OptOtherwise()

    def OptOtherwise(self) -> None:
        if self.current_token == "keyword" and self.current_lexeme == "otherwise":
            self._prod("<OptOtherwise> -> otherwise <CompoundStatement>")
            self.match_keyword("otherwise")
            self.CompoundStatement()
        else:
            self._prod("<OptOtherwise> -> ε")

    def While(self) -> None:
        self._prod("<While> -> while ( <Condition> ) <CompoundStatement>")
        self.match_keyword("while")
        self.match_separator("(")
        self.Condition()
        self.match_separator(")")
        self.CompoundStatement()

    def Return(self) -> None:
        self._prod("<Return> -> return <OptExpression> ;")
        self.match_keyword("return")
        self.OptExpression()
        self.match_separator(";")

    def OptExpression(self) -> None:
        if self.current_token == "separator" and self.current_lexeme == ";":
            self._prod("<OptExpression> -> ε")
            return
        self._prod("<OptExpression> -> <Expression>")
        self.Expression()

    def Print(self) -> None:
        self._prod("<Print> -> write ( <ExpressionList> ) ;")
        self.match_keyword("write")
        self.match_separator("(")
        self.ExpressionList()
        self.match_separator(")")
        self.match_separator(";")

    def Scan(self) -> None:
        self._prod("<Scan> -> read ( <IdentifierList> ) ;")
        self.match_keyword("read")
        self.match_separator("(")
        self.IdentifierList()
        self.match_separator(")")
        self.match_separator(";")

    def Assign(self) -> None:
        self._prod("<Assign> -> <Identifier> = <Expression> ;")
        self.match_token("identifier")
        self.match_operator("=")
        self.Expression()
        self.match_separator(";")

    def CallStatement(self) -> None:
        self._prod("<CallStatement> -> <Identifier> ( <ExpressionList> ) ;")
        self.match_token("identifier")
        self.match_separator("(")
        self.ExpressionList()
        self.match_separator(")")
        self.match_separator(";")

    def IdentifierList(self) -> None:
        self._prod("<IdentifierList> -> identifier <IdentifierListTail>")
        self.match_token("identifier")
        self.IdentifierListTail()

    def IdentifierListTail(self) -> None:
        if self.current_token == "separator" and self.current_lexeme == ",":
            self._prod("<IdentifierListTail> -> , identifier <IdentifierListTail>")
            self.match_separator(",")
            self.match_token("identifier")
            self.IdentifierListTail()
        else:
            self._prod("<IdentifierListTail> -> ε")

    def ExpressionList(self) -> None:
        if self.current_token == "separator" and self.current_lexeme == ")":
            self._prod("<ExpressionList> -> ε")
            return
        self._prod("<ExpressionList> -> <Expression> <ExpressionListTail>")
        self.Expression()
        self.ExpressionListTail()

    def ExpressionListTail(self) -> None:
        if self.current_token == "separator" and self.current_lexeme == ",":
            self._prod("<ExpressionListTail> -> , <Expression> <ExpressionListTail>")
            self.match_separator(",")
            self.Expression()
            self.ExpressionListTail()
        else:
            self._prod("<ExpressionListTail> -> ε")

    def Condition(self) -> None:
        self._prod("<Condition> -> <Expression> <RelExprPrime>")
        self.Expression()
        self.RelExprPrime()

    def RelExprPrime(self) -> None:
        if self.current_token == "operator" and self.current_lexeme in self.REL_OPS:
            op = self.current_lexeme
            self._prod(f"<RelExprPrime> -> {op} <Expression>")
            self.match_operator(op)
            self.Expression()
        else:
            self._prod("<RelExprPrime> -> ε")

    def Expression(self) -> None:
        self._prod("<Expression> -> <Term> <ExpressionPrime>")
        self.Term()
        self.ExpressionPrime()

    def ExpressionPrime(self) -> None:
        if self.current_token == "operator" and self.current_lexeme in ("+", "-"):
            op = self.current_lexeme
            self._prod(f"<ExpressionPrime> -> {op} <Term> <ExpressionPrime>")
            self.match_operator(op)
            self.Term()
            self.ExpressionPrime()
        else:
            self._prod("<ExpressionPrime> -> ε")

    def Term(self) -> None:
        self._prod("<Term> -> <Factor> <TermPrime>")
        self.Factor()
        self.TermPrime()

    def TermPrime(self) -> None:
        if self.current_token == "operator" and self.current_lexeme in ("*", "/"):
            op = self.current_lexeme
            self._prod(f"<TermPrime> -> {op} <Factor> <TermPrime>")
            self.match_operator(op)
            self.Factor()
            self.TermPrime()
        else:
            self._prod("<TermPrime> -> ε")

    def Factor(self) -> None:
        if self.current_token == "operator" and self.current_lexeme in ("+", "-"):
            op = self.current_lexeme
            self._prod(f"<Factor> -> {op} <Factor>")
            self.match_operator(op)
            self.Factor()
        else:
            self._prod("<Factor> -> <Primary>")
            self.Primary()

    def Primary(self) -> None:
        if self.current_token == "keyword" and self.current_lexeme in ("true", "false"):
            self._prod(f"<Primary> -> {self.current_lexeme}")
            self.match_keyword(self.current_lexeme)
        elif self.current_token == "integer":
            self._prod("<Primary> -> <Integer>")
            self.match_token("integer")
        elif self.current_token == "real":
            self._prod("<Primary> -> <Real>")
            self.match_token("real")
        elif self.current_token == "separator" and self.current_lexeme == "(":
            self._prod("<Primary> -> ( <Expression> )")
            self.match_separator("(")
            self.Expression()
            self.match_separator(")")
        elif self.current_token == "identifier":
            self._prod("<Primary> -> <Identifier> <OptArguments>")
            self.match_token("identifier")
            self.OptArguments()
        else:
            self._syntax_error("identifier, literal, true/false, or '('", f"{self.current_token} / {self.current_lexeme!r}")

    def OptArguments(self) -> None:
        if self.current_token == "separator" and self.current_lexeme == "(":
            self._prod("<OptArguments> -> ( <ExpressionList> )")
            self.match_separator("(")
            self.ExpressionList()
            self.match_separator(")")
        else:
            self._prod("<OptArguments> -> ε")


def parse_file(input_path: str, output_path: str, print_switch: bool = True) -> bool:
    with open(input_path, "r", encoding="utf-8") as f:
        source = f.read()
    raw = lexer(source)
    tokens: List[TokenRow] = []
    for row in raw:
        if len(row) >= 3:
            tokens.append((row[0], row[1], row[2]))
        else:
            tokens.append((row[0], row[1], 1))
    with open(output_path, "w", encoding="utf-8") as out:
        p = Parser(tokens, out)
        p.print_switch = print_switch
        try:
            p._advance()
            p.Rat26S()
            return True
        except ParseError:
            return False


print_switch = True


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python parser.py <input_file> <output_file>")
        sys.exit(1)
    ok = parse_file(sys.argv[1], sys.argv[2], print_switch=print_switch)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
