import codecs
from ply import lex


class Lexer(object):
    def __init__(self, **kwargs):
        self._lexer = lex.lex(module=self, **kwargs)
        self.errors = []

    def input(self, data):
        self._lexer.input(data)

    def token(self):
        return self._lexer.token()

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
        "bitfield": "BITFIELD",
        "enum": "ENUM",
        "AF": "AF",
        "QUERY": "QUERY",
        "WHERE": "WHERE",
        "VALUE": "VALUE",
        "UNIT": "UNIT",
        "BESTMOVE": "BESTMOVE",
        "MIN": "MIN",
        "MAX": "MAX",
        "AVE": "AVE",
        "SUM": "SUM",
    }

    tokens = (
        'ID',
        'LPAREN',
        'RPAREN',
        'COMMA',
        'DOT',
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
        'INT',
        'FLOAT',
        'STRING',
        'ASSIGN',
        'CODELITERAL',
        'LBRACKET',
        'RBRACKET',
        'ARROW',
        'DOUBLECOL',
        'VBAR',
    ) + tuple(reserved.values())

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','
    t_DOT = r'\.'
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
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_ARROW = r'->'
    t_DOUBLECOL = r'::'
    t_VBAR = r'\|'

    t_ignore_COMMENT = r'\#.*'

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        # See http://www.dabeaz.com/ply/ply.html#ply_nn6
        t.type = self.__class__.reserved.get(t.value, 'ID')
        return t

    def t_NUMBER(self, t):
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
            t.type = "INT"
        except ValueError:
            t.value = float(t.value)
            t.type = "FLOAT"
        return t

    def t_STRING(self, t):
        r'"([^\\"]*(?:\\.[^\\"]*)*)"'
        t.value = codecs.getdecoder("unicode_escape")(t.value[1:-1])[0]
        return t

    def t_CODELITERAL(self, t):
        r'`.+?`'
        t.value = t.value[1:-1]
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        self.errors.append((t.lineno, "invalid token %r" % t.value))
        t.lexer.skip(1)

    t_ignore = " \t"
