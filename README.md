# CS323-Compiler

**Course:** CPSC 323  
**Semester:** Spring 2026  
**Language Used:** Python

---

## Assignment 1: Lexical Analyzer (Rat26S)

The lexer is implemented in `Assignment1/python.py`.

### Features

- Tokenizes Rat26S source into:
  - `keyword`
  - `identifier`
  - `integer`
  - `real`
  - `operator`
  - `separator`
- Skips whitespace and `/* ... */` comments
- Tracks line numbers for each token
- Returns tokens as tuples: `(token_type, lexeme, line_number)`

---

## Assignment 2: Syntax Analyzer (Recursive Descent Parser)

The parser is implemented in `Assignment1/parser.py` and uses the lexer from Assignment 1.

### Parser behavior

- Top-down Recursive Descent Parser (LL(1)-style)
- Uses one function per grammar rule
- Prints parsing trace to output file:
  - `Token: <TokenType> Lexeme: <lexeme>`
  - Production rules used during parsing
- Supports both:
  - single-statement bodies
  - compound bodies with `{ ... }`
- Handles `if ... fi` and optional `otherwise ... fi`
- Reports syntax errors with line number, expected token, and actual token/lexeme

### Print switch

In `Assignment1/parser.py`, production rule printing is controlled by:

- `print_switch = True`  -> show production rules
- `print_switch = False` -> hide production rules

Token lines are always printed.

---

## Notes

- Output files are created in `Assignment1/` unless a different output path is provided.
- Some temporary debug files may exist from local testing (for example `sample_case.*` or `assign_stmt.*`).