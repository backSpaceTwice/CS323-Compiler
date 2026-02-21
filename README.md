# CS323-Compiler
## Assignment 1: Lexical Analyzer for Rat26S

**Course:** CPSC 323
**Semester:** Spring 2026
**Assignment:** 1 – Lexical Analyzer
**Language Used:** Python

---

## Project Description

This project implements a **Lexical Analyzer (Lexer)** for the Rat26S programming language.

The lexer reads a Rat26S source file and produces a sequence of tokens.
Each token contains:

- **Token Type** (keyword, identifier, integer, real, operator, separator)
- **Lexeme** (the actual string from the source file)

The output is written to an output file.

---

## Rat26S Language Overview

Rat26S is a simple imperative programming language with:

- Identifiers
- Integers
- Real numbers
- Keywords
- Operators
- Separators
- Comments (`/* comment */`)

Whitespace and comments are ignored by the lexer.

---