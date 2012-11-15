from redux.autorepr import AutoRepr
from redux.structeq import StructEq
from redux.types import Type


class ASTNode(AutoRepr, StructEq):
    pass


class Block(ASTNode):
    def __init__(self, statements, scope_overrides=None):
        self.statements = statements
        if scope_overrides is None:
            scope_overrides = []
        self.scope_overrides = scope_overrides


class FunctionCall(ASTNode):
    def __init__(self, function, arguments):
        self.function = function
        self.arguments = arguments


class ReturnStmt(ASTNode):
    def __init__(self, expression):
        self.expression = expression


class BreakStmt(ASTNode):
    pass


class CodeLiteral(ASTNode):
    def __init__(self, code):
        self.code = code


class Assignment(ASTNode):
    def __init__(self, variable, expression):
        self.variable = variable
        self.expression = expression


class BitfieldAssignment(Assignment):
    pass


class IfStmt(ASTNode):
    def __init__(self, condition, then_block, else_part=None):
        self.condition = condition
        self.then_block = then_block
        self.else_part = else_part


class WhileStmt(ASTNode):
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block


class FunctionDefinition(ASTNode):
    def __init__(self, name, arguments, block):
        self.name = name
        self.arguments = arguments
        self.block = block
        self.nontrivial = True


class BitfieldDefinition(ASTNode, Type):
    def __init__(self, name, members):
        self.name = name
        self.members = members

    def get_member_limits(self, member):
        offset = 0
        for name, length in self.members:
            if name == member:
                return offset, length

            offset += length

        raise KeyError(member)


class EnumDefinition(ASTNode, Type):
    def __init__(self, name, members):
        self.name = name
        computed_members = []

        counter = -1
        for name, value in members:
            if value is None:
                counter += 1
            else:
                assert value > counter
                counter = value

            computed_members.append((name, counter))

        self.members = computed_members


class Constant(ASTNode):
    def __init__(self, value, type_):
        self.value = value
        self.type = type_


class VarRef(ASTNode):
    def __init__(self, name):
        self.name = name


class BitfieldAccess(ASTNode):
    def __init__(self, variable, member):
        self.variable = variable
        self.member = member


class BinaryOp(ASTNode):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs


class AddOp(BinaryOp):
    pass


class SubOp(BinaryOp):
    pass


class MulOp(BinaryOp):
    pass


class DivOp(BinaryOp):
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


class LogicalNotOp(RelationalOp):
    def __init__(self, expression):
        self.expression = expression
