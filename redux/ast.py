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
    def __init__(self, variable_name, expression):
        self.variable_name = variable_name
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


class LessThanOp(BinaryOp):
    pass


class GreaterThanOp(BinaryOp):
    pass


class LessThanOrEqualToOp(BinaryOp):
    pass


class GreaterThanOrEqualToOp(BinaryOp):
    pass


class EqualToOp(BinaryOp):
    pass


class NotEqualToOp(BinaryOp):
    pass


class LogicalAndOp(BinaryOp):
    pass


class LogicalOrOp(BinaryOp):
    pass


class LogicalNotOp(ASTNode):
    def __init__(self, expression):
        self.expression = expression
