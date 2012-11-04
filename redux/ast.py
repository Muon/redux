import codecs
from redux.autorepr import AutoRepr
from redux.structeq import StructEq


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


class BitfieldDefinition(ASTNode):
    def __init__(self, name, members):
        self.name = name
        self.members = members

    def get_member_limits(self, member):
        total_length = 0
        for name, length in self.members:
            if name == member:
                return total_length, length

            total_length += length

        raise KeyError(member)


class EnumDefinition(ASTNode):
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
    def __init__(self, value):
        self.value = value

    def get_value(self):
        if isinstance(self.value, int) or isinstance(self.value, float):
            return repr(self.value)
        else:
            return "\"" + codecs.getencoder("unicode_escape")(self.value)[0].decode("utf8") + "\""


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


class LessThanOp(BinaryOp, RelationalOp):
    pass


class GreaterThanOp(BinaryOp, RelationalOp):
    pass


class LessThanOrEqualToOp(BinaryOp, RelationalOp):
    pass


class GreaterThanOrEqualToOp(BinaryOp, RelationalOp):
    pass


class EqualToOp(BinaryOp, RelationalOp):
    pass


class NotEqualToOp(BinaryOp, RelationalOp):
    pass


class LogicalAndOp(BinaryOp, RelationalOp):
    pass


class LogicalOrOp(BinaryOp, RelationalOp):
    pass


class LogicalNotOp(RelationalOp):
    def __init__(self, expression):
        self.expression = expression
