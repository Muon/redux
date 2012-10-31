from ply import yacc
from lexer import lexer, tokens
from ast import *


def report_syntax_error(lineno, message):
    sys.stderr.write("%s:%d: %s\n" % (filename, lineno, message))


def p_block(p):
    "block : stmt_list"
    p[0] = Block(p[1])


def p_stmt_list(p):
    "stmt_list : stmt_list stmt"
    p[0] = p[1] + [p[2]]


def p_stmt_list_empty(p):
    "stmt_list : empty"
    p[0] = []


def p_stmt(p):
    """
    stmt : func_call
         | assignment
         | if_stmt
         | while_stmt
         | func_def
         | code_literal
         | break_stmt
         | bitfield_def
    """
    p[0] = p[1]


def p_func_call(p):
    "func_call : ID LPAREN arg_list RPAREN"
    p[0] = FunctionCall(p[1], p[3])


def p_assignment(p):
    "assignment : variable ASSIGN expression"
    p[0] = Assignment(p[1], p[3])


def p_assignment_error(p):
    "assignment : variable ASSIGN error"
    report_syntax_error(p.lineno(-1), "expected expression after start of assignment")


def p_stray_variable_err(p):
    "stmt : variable error"
    report_syntax_error(p.lineno(-1), "stray identifier '%s'" % p[1].name)


def p_code_literal(p):
    "code_literal : CODELITERAL"
    p[0] = CodeLiteral(p[1])


def p_else_part_empty(p):
    "else_part : END"
    p[0] = None


def p_else_part(p):
    "else_part : ELSE block END"
    p[0] = p[2]


def p_elif_part_empty(p):
    "elif_part : else_part"
    p[0] = p[1]


def p_elif_part(p):
    "elif_part : ELIF expression block elif_part"
    p[0] = Block([IfStmt(p[2], p[3], p[4])])


def p_if_stmt(p):
    "if_stmt : IF expression block elif_part"
    p[0] = IfStmt(p[2], p[3], p[4])


def p_while_stmt(p):
    "while_stmt : WHILE expression block END"
    p[0] = WhileStmt(p[2], p[3])


def p_return_stmt(p):
    "return_stmt : RETURN expression"
    p[0] = ReturnStmt(p[2])


def p_break_stmt(p):
    "break_stmt : BREAK"
    p[0] = BreakStmt()


def p_func_def(p):
    "func_def : DEF ID LPAREN id_list RPAREN block return_stmt END"
    p[0] = FunctionDefinition(p[2], p[4], Block(p[6].statements + [p[7]]))


def p_func_def_noreturn(p):
    "func_def : DEF ID LPAREN id_list RPAREN block END"
    p[0] = FunctionDefinition(p[2], p[4], p[6])


def p_variable(p):
    "variable : ID"
    p[0] = VarRef(p[1])


def p_constant(p):
    """
    constant : NUMBER
             | STRING
    """
    p[0] = Constant(p[1])


def p_value(p):
    """
    value : variable
          | constant
    """
    p[0] = p[1]


def p_expression_value(p):
    "expression : value"
    p[0] = p[1]


def p_expression_call(p):
    "expression : func_call"
    p[0] = p[1]


def p_expression_paren(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]

precedence = (
    ('nonassoc', 'LT', 'GT', 'LTE', 'GTE', 'EQ', 'NEQ'),
    ('left', 'LOR'),
    ('left', 'LAND'),
    ('right', 'LNOT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)


# DO NOT MOVE THIS UP: PLY sorts productions by the line they were defined at
# i.e. if it is moved to the top, it will become the initial production
def binary_expr(cls, token):
    def production(p):
        p[0] = cls(p[1], p[3])

    production.__doc__ = "expression : expression " + token + " expression"
    production.__name__ = "p_expression_bin_" + token.lower()
    globals()[production.__name__] = production

binary_expr(AddOp, 'PLUS')
binary_expr(SubOp, 'MINUS')
binary_expr(MulOp, 'TIMES')
binary_expr(DivOp, 'DIVIDE')
binary_expr(LessThanOp, 'LT')
binary_expr(GreaterThanOp, 'GT')
binary_expr(LessThanOrEqualToOp, 'LTE')
binary_expr(GreaterThanOrEqualToOp, 'GTE')
binary_expr(EqualToOp, 'EQ')
binary_expr(NotEqualToOp, 'NEQ')
binary_expr(LogicalOrOp, 'LOR')
binary_expr(LogicalAndOp, 'LAND')


def p_lnot(p):
    "expression : LNOT expression"
    p[0] = LogicalNotOp(p[2])


def p_empty(p):
    "empty : "
    pass


def p_arg_list_empty(p):
    "arg_list : empty"
    p[0] = []


def p_arg_list_single(p):
    "arg_list : expression"
    p[0] = [p[1]]


def p_arg_list(p):
    "arg_list : arg_list COMMA expression"
    p[0] = p[1] + [p[3]]


def p_arg_list_missing_comma_err(p):
    "arg_list : arg_list error expression"
    report_syntax_error(p.lineno(2), "expected ',' after argument %d" % len(p[1]))


def p_id_list_empty(p):
    "id_list : empty"
    p[0] = []


def p_id_list_single(p):
    "id_list : ID"
    p[0] = [p[1]]


def p_id_list(p):
    "id_list : id_list COMMA ID"
    p[0] = p[1] + [p[3]]


def p_bitfield_member_def(p):
    "bitfield_member_def : ID COLON NUMBER"
    p[0] = (p[1], p[3])


def p_bitfield_member_list_start(p):
    "bitfield_member_list : bitfield_member_def"
    p[0] = [p[1]]


def p_bitfield_member_list(p):
    "bitfield_member_list : bitfield_member_list bitfield_member_def"
    p[0] = p[1] + [p[2]]


def p_bitfield_def(p):
    "bitfield_def : BITFIELD ID bitfield_member_list END"
    p[0] = BitfieldDefinition(p[2], p[3])


def p_error(p):
    if p is None:
        lineno = 0
    else:
        lineno = p.lineno

    if p is None:
        report_syntax_error(lineno, "premature end-of-file encountered")

parser = yacc.yacc()


def parse(code):
    return parser.parse(code, lexer=lexer)
