from redux.autorepr import AutoRepr
from redux.ast import (Block, FunctionDefinition, CodeLiteral, ReturnStmt,
                       VarRef)

class IntrinsicFunction(AutoRepr):
    @property
    def nontrivial(self):
        return False


class SayFunction(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) > 0

        code_generator.emit("say ")
        code_generator.visit(args[0])
        for arg in args[1:]:
            code_generator.emit(", ")
            code_generator.visit(arg)

    def type(self, code_generator, args):
        return None


class SqrtFunction(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 1
        arg_type = code_generator.expression_type(args[0])
        assert arg_type == int or arg_type == float

        code_generator.emit("(|/")
        code_generator.visit(args[0])
        code_generator.emit(")")

    def type(self, code_generator, args):
        return float

GetAchronalField = lambda: FunctionDefinition("__get_achronal_field", ["num"], Block([CodeLiteral("PERFORM GET_ACHRONAL_FIELD num;"), ReturnStmt(VarRef("perf_ret"))]))
SetAchronalField = lambda: FunctionDefinition("__set_achronal_field", ["num", "value"], Block([CodeLiteral("target = num; PERFORM SET_ACHRONAL_FIELD value;")]))
