from ply import lex
import codecs
import sys

reserved = {
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "while": "WHILE",
    "end": "END",
    "and": "LAND",
    "or": "LOR",
    "not": "LNOT",
    "def": "DEF",
    "return": "RETURN",
    "break": "BREAK",
    "bitfield": "BITFIELD"
}

tokens = (
    'ID',
    'LPAREN',
    'RPAREN',
    'COMMA',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LT',
    'GT',
    'LTE',
    'GTE',
    'EQ',
    'NEQ',
    'COLON',
    'NUMBER',
    'STRING',
    'ASSIGN',
    'CODELITERAL',
) + tuple(reserved.values())

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'\/'
t_LT = r'<'
t_GT = r'>'
t_LTE = r'<='
t_GTE = r'>='
t_EQ = r'=='
t_NEQ = r'!='
t_ASSIGN = r'='
t_COLON = r':'

t_ignore_COMMENT = r'\#.*'


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')    # Check for reserved words
    return t


def t_NUMBER(t):
    r"""
    [-+]? # optional sign
    (?:
     (?: \d* \. \d+ ) # .1 .12 .123 etc 9.1 etc 98.1 etc
     |
     (?: \d+ \.? ) # 1. 12. 123. etc 1 12 123 etc
    )
    # followed by optional exponent part if desired
    (?: [Ee] [+-]? \d+ ) ?
    """
    try:
        t.value = int(t.value)
    except ValueError:
        t.value = float(t.value)

    return t


def t_STRING(t):
    r'"([^\\"]*(?:\\.[^\\"]*)*)"'

    t.value = codecs.getdecoder("unicode_escape")(t.value[1:-1])[0]
    return t


def t_CODELITERAL(t):
    r'`.+?`'
    t.value = t.value[1:-1]
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    sys.stderr.write("%s:%d: invalid token %r\n" % (filename, t.lineno, t.value))
    t.lexer.skip(1)

t_ignore = " \t"

lexer = lex.lex()
