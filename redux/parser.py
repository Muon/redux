from ply import yacc
from redux.ast import (Block, Assignment, BitfieldAssignment, WhileStmt, IfStmt,
                       FunctionCall, BreakStmt, ReturnStmt, CodeLiteral,
                       BitfieldDefinition, EnumDefinition, FunctionDefinition,
                       Constant, VarRef, DottedAccess, AddOp, SubOp, MulOp,
                       DivOp, EqualToOp, NotEqualToOp, GreaterThanOp,
                       GreaterThanOrEqualToOp, LessThanOp, LessThanOrEqualToOp,
                       LogicalNotOp, LogicalAndOp, LogicalOrOp, ExprStmt,
                       ChronalAccess, ClassAccess, Query, BitwiseOrOp)
from redux.lexer import Lexer
from redux.types import str_, int_, float_


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
        stmt : assignment
             | if_stmt
             | while_stmt
             | func_def
             | code_literal
             | break_stmt
             | bitfield_def
             | enum_def
        """
        p[0] = p[1]

    def p_stmt_func_call(self, p):
        "stmt : func_call"
        p[0] = ExprStmt(p[1])

    def p_func_call(self, p):
        "func_call : ID LPAREN arg_list RPAREN"
        p[0] = FunctionCall(p[1], p[3])

    def p_assignment(self, p):
        "assignment : variable ASSIGN expression"
        p[0] = Assignment(p[1], p[3])

    def p_bitfield_assignment(self, p):
        "assignment : variable DOT ID ASSIGN expression"
        p[0] = BitfieldAssignment(DottedAccess(p[1], p[3]), p[5])

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

    def p_constant_int(self, p):
        "constant : INT"
        p[0] = Constant(p[1], int_)

    def p_constant_float(self, p):
        "constant : FLOAT"
        p[0] = Constant(p[1], float_)

    def p_constant_string(self, p):
        "constant : STRING"
        p[0] = Constant(p[1], str_)

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

    def p_expression_paren(self, p):
        "expression : LPAREN expression RPAREN"
        p[0] = p[2]

    def p_expression_chronal_access(self, p):
        "expression : expression ARROW ID"
        p[0] = ChronalAccess(p[1], p[3])

    def p_expression_class_access(self, p):
        "expression : expression DOUBLECOL ID"
        p[0] = ClassAccess(p[1], p[3])

    precedence = (
        ('nonassoc', 'LOWERQUERY'),
        ('right', 'WHERE'),
        ('left', 'LOR'),
        ('left', 'LAND'),
        ('right', 'LNOT'),
        ('nonassoc', 'LT', 'GT', 'LTE', 'GTE', 'EQ', 'NEQ'),
        ('left', 'VBAR'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'ARROW', 'DOT', 'DOUBLECOL')
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
        "bitfield_member_def : ID COLON INT"
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

    def p_expression_dotted_access(self, p):
        "expression : expression DOT ID"
        p[0] = DottedAccess(p[1], p[3])

    def p_enum_def(self, p):
        "enum_def : ENUM ID enum_member_list END"
        p[0] = EnumDefinition(p[2], p[3])

    def p_enum_member_list_start(self, p):
        "enum_member_list : enum_member"
        p[0] = [p[1]]

    def p_enum_member_list(self, p):
        "enum_member_list : enum_member_list enum_member"
        p[0] = p[1] + [p[2]]

    def p_enum_member(self, p):
        "enum_member : ID"
        p[0] = (p[1], None)

    def p_enum_member_numbered(self, p):
        "enum_member : ID ASSIGN INT"
        p[0] = (p[1], p[3])

    def p_achronal_field_ref(self, p):
        "achronal_field_ref : AF LBRACKET expression RBRACKET"
        p[0] = p[3]

    def p_achronal_field_ref_expr(self, p):
        "expression : achronal_field_ref"
        p[0] = FunctionCall("__get_achronal_field", [p[1]])

    def p_achronal_field_assignment(self, p):
        "stmt : achronal_field_ref ASSIGN expression"
        p[0] = ExprStmt(FunctionCall("__set_achronal_field", [p[1], p[3]]))

    def p_active_unit(self, p):
        "active_unit : expression"
        p[0] = p[1]

    def p_active_unit_empty(self, p):
        "active_unit : empty"
        p[0] = VarRef("unit")

    def p_value_query_op_type(self, p):
        """
        value_query_op_type : MAX
                            | MIN
                            | SUM
                            | AVE
        """
        p[0] = p[1]

    def p_unit_query_op_type(self, p):
        """
        unit_query_op_type : MAX
                           | MIN
        """
        p[0] = p[1]

    def p_value_query(self, p):
        "expression : QUERY VALUE active_unit value_query_op_type expression WHERE expression"
        p[0] = Query(p[2], p[3], p[4], p[5], p[7])

    def p_unit_query(self, p):
        "expression : QUERY UNIT active_unit unit_query_op_type expression WHERE expression"
        p[0] = Query(p[2], p[3], p[4], p[5], p[7])

    def p_unit_query_criterionless(self, p):
        "expression : QUERY UNIT active_unit WHERE expression"
        p[0] = Query(p[2], p[3], "MIN", Constant(1, int_), p[5])

    def p_bestmove_query(self, p):
        "expression : QUERY BESTMOVE active_unit MIN expression WHERE expression"
        p[0] = Query(p[2], p[3], p[4], p[5], p[7])

    def p_value_query_wo(self, p):
        "expression : QUERY VALUE active_unit value_query_op_type expression %prec LOWERQUERY"
        p[0] = Query(p[2], p[3], p[4], p[5], Constant(1, int_))

    def p_unit_query_wo(self, p):
        "expression : QUERY UNIT active_unit unit_query_op_type expression %prec LOWERQUERY"
        p[0] = Query(p[2], p[3], p[4], p[5], Constant(1, int_))

    def p_bestmove_query_wo(self, p):
        "expression : QUERY BESTMOVE active_unit MIN expression %prec LOWERQUERY"
        p[0] = Query(p[2], p[3], p[4], p[5], Constant(1, int_))

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
binary_expr(BitwiseOrOp, 'VBAR')

_parser = Parser()


def parse(code):
    return _parser.parse(code)
