from ply import yacc
from redux.ast import (Block, Assignment, WhileStmt, IfStmt, FunctionCall,
                       BreakStmt, ReturnStmt, CodeLiteral, BitfieldDefinition,
                       FunctionDefinition, Constant, VarRef, BitfieldAccess,
                       AddOp, SubOp, MulOp, DivOp, EqualToOp, NotEqualToOp,
                       GreaterThanOp, GreaterThanOrEqualToOp, LessThanOp,
                       LessThanOrEqualToOp, LogicalNotOp, LogicalAndOp,
                       LogicalOrOp)
from redux.lexer import Lexer


class Parser(object):
    tokens = Lexer.tokens

    def __init__(self, **kwargs):
        self._parser = yacc.yacc(module=self, **kwargs)

    def parse(self, code):
        self.errors = []
        return self._parser.parse(code, lexer=Lexer()), self.errors

    def error(self, lineno, message):
        self.errors.append((lineno, message))

    def p_block(self, p):
        "block : stmt_list"
        p[0] = Block(p[1])

    def p_stmt_list(self, p):
        "stmt_list : stmt_list stmt"
        p[0] = p[1] + [p[2]]

    def p_stmt_list_empty(self, p):
        "stmt_list : empty"
        p[0] = []

    def p_stmt(self, p):
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

    def p_func_call(self, p):
        "func_call : ID LPAREN arg_list RPAREN"
        p[0] = FunctionCall(p[1], p[3])

    def p_assignment(self, p):
        """
        assignment : variable ASSIGN expression
                   | bitfield_access ASSIGN expression
        """
        p[0] = Assignment(p[1], p[3])

    def p_assignment_error(self, p):
        "assignment : variable ASSIGN error"
        self.error(p.lineno(3), "expected expression after start of assignment")

    def p_stray_variable_err(self, p):
        "stmt : variable error"
        self.error(p.lineno(1), "stray identifier '%s'" % p[1].name)

    def p_code_literal(self, p):
        "code_literal : CODELITERAL"
        p[0] = CodeLiteral(p[1])

    def p_else_part_empty(self, p):
        "else_part : END"
        p[0] = None

    def p_else_part(self, p):
        "else_part : ELSE block END"
        p[0] = p[2]

    def p_elif_part_empty(self, p):
        "elif_part : else_part"
        p[0] = p[1]

    def p_elif_part(self, p):
        "elif_part : ELIF expression block elif_part"
        p[0] = Block([IfStmt(p[2], p[3], p[4])])

    def p_if_stmt(self, p):
        "if_stmt : IF expression block elif_part"
        p[0] = IfStmt(p[2], p[3], p[4])

    def p_while_stmt(self, p):
        "while_stmt : WHILE expression block END"
        p[0] = WhileStmt(p[2], p[3])

    def p_return_stmt(self, p):
        "return_stmt : RETURN expression"
        p[0] = ReturnStmt(p[2])

    def p_break_stmt(self, p):
        "break_stmt : BREAK"
        p[0] = BreakStmt()

    def p_func_def(self, p):
        "func_def : DEF ID LPAREN id_list RPAREN block return_stmt END"
        p[0] = FunctionDefinition(p[2], p[4], Block(p[6].statements + [p[7]]))

    def p_func_def_noreturn(self, p):
        "func_def : DEF ID LPAREN id_list RPAREN block END"
        p[0] = FunctionDefinition(p[2], p[4], p[6])

    def p_variable(self, p):
        "variable : ID"
        p[0] = VarRef(p[1])

    def p_constant(self, p):
        """
        constant : NUMBER
                 | STRING
        """
        p[0] = Constant(p[1])

    def p_value(self, p):
        """
        value : variable
              | constant
        """
        p[0] = p[1]

    def p_expression_value(self, p):
        "expression : value"
        p[0] = p[1]

    def p_expression_call(self, p):
        "expression : func_call"
        p[0] = p[1]

    def p_expression_bitfield_access(self, p):
        "expression : bitfield_access"
        p[0] = p[1]

    def p_expression_paren(self, p):
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

    def p_lnot(self, p):
        "expression : LNOT expression"
        p[0] = LogicalNotOp(p[2])

    def p_empty(self, p):
        "empty : "
        pass

    def p_arg_list_empty(self, p):
        "arg_list : empty"
        p[0] = []

    def p_arg_list_single(self, p):
        "arg_list : expression"
        p[0] = [p[1]]

    def p_arg_list(self, p):
        "arg_list : arg_list COMMA expression"
        p[0] = p[1] + [p[3]]

    def p_arg_list_missing_comma_err(self, p):
        "arg_list : arg_list error expression"
        self.error(p.lineno(2), "expected ',' after argument %d" % len(p[1]))

    def p_id_list_empty(self, p):
        "id_list : empty"
        p[0] = []

    def p_id_list_single(self, p):
        "id_list : ID"
        p[0] = [p[1]]

    def p_id_list(self, p):
        "id_list : id_list COMMA ID"
        p[0] = p[1] + [p[3]]

    def p_bitfield_member_def(self, p):
        "bitfield_member_def : ID COLON NUMBER"
        p[0] = (p[1], p[3])

    def p_bitfield_member_list_start(self, p):
        "bitfield_member_list : bitfield_member_def"
        p[0] = [p[1]]

    def p_bitfield_member_list(self, p):
        "bitfield_member_list : bitfield_member_list bitfield_member_def"
        p[0] = p[1] + [p[2]]

    def p_bitfield_def(self, p):
        "bitfield_def : BITFIELD ID bitfield_member_list END"
        p[0] = BitfieldDefinition(p[2], p[3])

    def p_bitfield_access(self, p):
        "bitfield_access : variable DOT ID"
        p[0] = BitfieldAccess(p[1], p[3])

    def p_error(self, p):
        if p is None:
            lineno = 0
        else:
            lineno = p.lineno
        if p is None:
            self.error(lineno, "premature end-of-file encountered")
        else:
            self.error(lineno, "syntax error")


# DO NOT MOVE THIS UP: PLY sorts productions by the line they were defined at
# i.e. if it is moved to the top, it will become the initial production
def binary_expr(cls, token):
    def production(self, p):
        p[0] = cls(p[1], p[3])

    production.__doc__ = "expression : expression " + token + " expression"
    production.__name__ = "p_expression_bin_" + token.lower()
    setattr(Parser, production.__name__, production)

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

_parser = Parser()


def parse(code):
    return _parser.parse(code)
