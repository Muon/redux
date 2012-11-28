from nose.tools import eq_
from redux.ast import (Block, Assignment, WhileStmt, IfStmt, FunctionCall,
                       BreakStmt, ReturnStmt, CodeLiteral, BitfieldDefinition,
                       EnumDefinition, DottedAccess, BitfieldAssignment,
                       FunctionDefinition, Constant, VarRef, AddOp, EqualToOp,
                       GreaterThanOp, LogicalNotOp, ChronalAccess, ClassAccess,
                       LogicalAndOp, Query, BitwiseOrOp, BitwiseXorOp)
from redux.parser import parse
from redux.types import int_, str_


def test_valid_parses():
    valid_parses = [
        ("a = 1", Block([Assignment(VarRef("a"), Constant(1, int_))])),
        ("a = \"abc\"", Block([Assignment(VarRef("a"), Constant("abc", str_))])),
        ("a = a + b", Block([Assignment(VarRef("a"), AddOp(VarRef("a"), VarRef("b")))])),
        ("a = f()", Block([Assignment(VarRef("a"), FunctionCall("f", []))])),
        ("a = f(1, 2)", Block([Assignment(VarRef("a"), FunctionCall("f", [Constant(1, int_), Constant(2, int_)]))])),
        ("if a == 0 end", Block([IfStmt(EqualToOp(VarRef("a"), Constant(0, int_)), Block([]))])),
        ("if a == 0 else end", Block([IfStmt(EqualToOp(VarRef("a"), Constant(0, int_)), Block([]), Block([]))])),
        ("if a == 0 elif b == 0 else end", Block([IfStmt(EqualToOp(VarRef('a'), Constant(0, int_)), Block([]), Block([IfStmt(EqualToOp(VarRef('b'), Constant(0, int_)), Block([]), Block([]))]))])),
        ("`PERFORM RAND;`", Block([CodeLiteral("PERFORM RAND;")])),
        ("while a > 0 end", Block([WhileStmt(GreaterThanOp(VarRef("a"), Constant(0, int_)), Block([]))])),
        ("break", Block([BreakStmt()])),
        ("def f() return 1 end", Block([FunctionDefinition("f", [], Block([ReturnStmt(Constant(1, int_))]))])),
        ("def f(a, b) end", Block([FunctionDefinition("f", ["a", "b"], Block([]))])),
        ("a = (b)", Block([Assignment(VarRef("a"), VarRef("b"))])),
        ("bitfield A x : 8 y : 8 end", Block([BitfieldDefinition("A", [("x", 8), ("y", 8)])])),
        ("a.x = 0", Block([BitfieldAssignment(DottedAccess(VarRef("a"), "x"), Constant(0, int_))])),
        ("a = not a", Block([Assignment(VarRef("a"), LogicalNotOp(VarRef("a")))])),
        ("enum X a b end", Block([EnumDefinition('X', [('a', 0), ('b', 1)])])),
        ("enum X a = 1 b end", Block([EnumDefinition('X', [('a', 1), ('b', 2)])])),
        ("a = unit->Timestamp", Block([Assignment(VarRef("a"), ChronalAccess(VarRef("unit"), "Timestamp"))])),
        ("a = 1::Rank", Block([Assignment(VarRef("a"), ClassAccess(Constant(1, int_), "Rank"))])),
        ("a = 2 > 0 and 1 > 0", Block([Assignment(VarRef('a'), LogicalAndOp(GreaterThanOp(Constant(2, 'int,'), Constant(0, 'int,')), GreaterThanOp(Constant(1, 'int,'), Constant(0, 'int,'))), False)])),
        ("a = (QUERY VALUE SUM 1 WHERE unit->HP > 0 and 1 > 0)", Block([Assignment(VarRef("a"), Query("VALUE", VarRef("unit"), "SUM", Constant(1, int_), LogicalAndOp(GreaterThanOp(ChronalAccess(VarRef("unit"), "HP"), Constant(0, int_)), GreaterThanOp(Constant(1, int_), Constant(0, int_)))))])),
        ("a = (QUERY UNIT WHERE query->HP > 100)", Block([Assignment(VarRef('a'), Query('UNIT', VarRef('unit'), 'MIN', Constant(1, 'int,'), GreaterThanOp(ChronalAccess(VarRef('query'), 'HP'), Constant(100, 'int,'))))])),
        ("a = (QUERY BESTMOVE target MIN query->XPosition)", Block([Assignment(VarRef("a"), Query("BESTMOVE", VarRef("target"), "MIN", ChronalAccess(VarRef("query"), "XPosition"), Constant(1, int_)))])),
        ("a = (QUERY UNIT MIN query->HP)", Block([Assignment(VarRef('a'), Query('UNIT', VarRef('unit'), 'MIN', ChronalAccess(VarRef('query'), 'HP'), Constant(1, 'int,')))])),
        ("a = (QUERY UNIT MIN 1 WHERE query->HP)", Block([Assignment(VarRef('a'), Query('UNIT', VarRef('unit'), 'MIN', Constant(1, 'int,'), ChronalAccess(VarRef('query'), 'HP')))])),
        ("a = QUERY VALUE SUM 1 WHERE unit->HP > 0 and 1 > 0", Block([Assignment(VarRef("a"), Query("VALUE", VarRef("unit"), "SUM", Constant(1, int_), LogicalAndOp(GreaterThanOp(ChronalAccess(VarRef("unit"), "HP"), Constant(0, int_)), GreaterThanOp(Constant(1, int_), Constant(0, int_)))))])),
        ("a = QUERY UNIT WHERE query->HP > 100", Block([Assignment(VarRef('a'), Query('UNIT', VarRef('unit'), 'MIN', Constant(1, 'int,'), GreaterThanOp(ChronalAccess(VarRef('query'), 'HP'), Constant(100, 'int,'))))])),
        ("a = QUERY BESTMOVE target MIN query->XPosition", Block([Assignment(VarRef("a"), Query("BESTMOVE", VarRef("target"), "MIN", ChronalAccess(VarRef("query"), "XPosition"), Constant(1, int_)))])),
        ("a = QUERY UNIT MIN query->HP", Block([Assignment(VarRef('a'), Query('UNIT', VarRef('unit'), 'MIN', ChronalAccess(VarRef('query'), 'HP'), Constant(1, 'int,')))])),
        ("a = QUERY UNIT MIN 1 WHERE query->HP", Block([Assignment(VarRef('a'), Query('UNIT', VarRef('unit'), 'MIN', Constant(1, 'int,'), ChronalAccess(VarRef('query'), 'HP')))])),
        ("a = QUERY UNIT MIN QUERY VALUE query SUM 1 WHERE query->HP > 0", Block([Assignment(VarRef('a'), Query('UNIT', VarRef('unit'), 'MIN', Query('VALUE', VarRef('query'), 'SUM', Constant(1, int_), GreaterThanOp(ChronalAccess(VarRef('query'), 'HP'), Constant(0, int_))), Constant(1, int_)))])),
        ("a = QUERY BESTMOVE MIN 1 WHERE 1", Block([Assignment(VarRef('a'), Query('BESTMOVE', VarRef('unit'), 'MIN', Constant(1, 'int,'), Constant(1, 'int,')))])),
        ("a = 1 | 4", Block([Assignment(VarRef('a'), BitwiseOrOp(Constant(1, int_), Constant(4, int_)))])),
        ("a = 1 ^ 4", Block([Assignment(VarRef('a'), BitwiseXorOp(Constant(1, int_), Constant(4, int_)))])),
    ]

    for code, ast_ in valid_parses:
        yield check_valid_parse, code, ast_


def check_valid_parse(code, ast_):
    compiled_ast, errors = parse(code)
    eq_(errors, [])
    eq_(compiled_ast, ast_)
