from redux.autorepr import AutoRepr
from redux.ast import (Block, FunctionDefinition, CodeLiteral, ReturnStmt,
                       VarRef)
from redux.types import float_, is_numeric

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

    @property
    def type(self):
        return None


class SqrtFunction(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 1
        assert is_numeric(args[0].type)

        code_generator.emit("(|/")
        code_generator.visit(args[0])
        code_generator.emit(")")

    @property
    def type(self):
        return float_

GetAchronalField = lambda: FunctionDefinition("__get_achronal_field", ["num"], Block([CodeLiteral("PERFORM GET_ACHRONAL_FIELD num;"), ReturnStmt(VarRef("perf_ret"))]))
SetAchronalField = lambda: FunctionDefinition("__set_achronal_field", ["num", "value"], Block([CodeLiteral("target = num; PERFORM SET_ACHRONAL_FIELD value;")]))
