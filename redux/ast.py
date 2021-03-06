from redux.types import int_

class ASTNode(object):
    """Base class of all AST nodes."""
    _fields = []

    def __init__(self, *args):
        assert len(args) == len(self._fields), "field/argument length mismatch"

        super(ASTNode, self).__init__()

        for name, value in zip(self._fields, args):
            setattr(self, name, value)

    # Inspired by the standard ast module
    def fields(self):
        for field in self._fields:
            try:
                yield field, getattr(self, field)
            except AttributeError:
                pass

    def children(self):
        for name, value in self.fields():
            if isinstance(value, ASTNode):
                yield value
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        yield item

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join(repr(getattr(self, name)) for name in self._fields))


class Stmt(ASTNode):
    pass


class Expr(ASTNode):
    pass


class Block(Stmt):
    _fields = ["statements"]


class Require(Stmt):
    _fields = ["path"]


class ExprStmt(Stmt):
    _fields = ["expression"]


class FunctionCall(Expr):
    _fields = ["function", "arguments"]


class ReturnStmt(Stmt):
    _fields = ["expression"]


class BreakStmt(Stmt):
    pass


class CodeLiteral(Stmt):
    _fields = ["code"]


class Assignment(Stmt):
    _fields = ["variable", "expression", "declare"]

    def __init__(self, variable, expression, declare=False):
        super(Assignment, self).__init__(variable, expression, declare)


class BitfieldAssignment(Assignment):
    pass


class IfStmt(Stmt):
    _fields = ["condition", "then_block", "else_part"]

    def __init__(self, condition, then_block, else_part=None):
        super(IfStmt, self).__init__(condition, then_block, else_part)


class WhileStmt(Stmt):
    _fields = ["condition", "block"]


class ForStmt(Stmt):
    _fields = ["assignment", "condition", "step_expr", "block"]


class FunctionDefinition(Stmt):
    _fields = ["name", "arguments", "block", "nontrivial"]

    def __init__(self, name, arguments, block):
        super(Stmt, self).__init__(name, arguments, block, True)


class BitfieldDefinition(Stmt):
    _fields = ["name", "members"]

    def get_member_limits(self, member):
        offset = 0
        for name, length in self.members:
            if name == member:
                return offset, length

            offset += length

        raise KeyError(member)


class EnumDefinition(Stmt):
    _fields = ["name", "members"]

    def __init__(self, name, members):
        computed_members = []

        counter = -1
        for member_name, value in members:
            if value is None:
                counter += 1
            else:
                assert value > counter
                counter = value

            computed_members.append((member_name, Constant(counter, int_)))

        super(Stmt, self).__init__(name, computed_members)


class Constant(Expr):
    _fields = ["value", "type"]


class VarRef(Expr):
    _fields = ["name"]


class DottedAccess(Expr):
    _fields = ["expression", "member"]


class ChronalAccess(Expr):
    _fields = ["object", "member"]


class ClassAccess(Expr):
    _fields = ["class_", "member"]


class Query(Expr):
    _fields = ["query_type", "unit", "op", "op_expr", "where_cond"]

class NoOp(Expr):
    pass

class BinaryOp(Expr):
    _fields = ["lhs", "rhs"]


class AddOp(BinaryOp):
    pass


class SubOp(BinaryOp):
    pass


class MulOp(BinaryOp):
    pass


class DivOp(BinaryOp):
    pass


class ModuloOp(BinaryOp):
    pass


class PowerOp(BinaryOp):
    pass


class BitwiseOp(ASTNode):
    pass


class BitwiseOrOp(BitwiseOp, BinaryOp):
    pass


class BitwiseXorOp(BitwiseOp, BinaryOp):
    pass


class BitwiseAndOp(BitwiseOp, BinaryOp):
    pass


class BitwiseLeftShiftOp(BitwiseOp, BinaryOp):
    pass


class BitwiseRightShiftOp(BitwiseOp, BinaryOp):
    pass


class RelationalOp(ASTNode):
    pass


class LessThanOp(RelationalOp, BinaryOp):
    pass


class GreaterThanOp(RelationalOp, BinaryOp):
    pass


class LessThanOrEqualToOp(RelationalOp, BinaryOp):
    pass


class GreaterThanOrEqualToOp(RelationalOp, BinaryOp):
    pass


class EqualToOp(RelationalOp, BinaryOp):
    pass


class NotEqualToOp(RelationalOp, BinaryOp):
    pass


class LogicalAndOp(RelationalOp, BinaryOp):
    pass


class LogicalOrOp(RelationalOp, BinaryOp):
    pass


class UnaryOp(Expr):
    _fields = ["expression"]


class NegateOp(UnaryOp):
    pass


class BitwiseNotOp(BitwiseOp, UnaryOp):
    pass


class LogicalNotOp(RelationalOp, UnaryOp):
    pass
