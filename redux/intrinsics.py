from redux.ast import (Block, FunctionDefinition, CodeLiteral, ReturnStmt,
                       VarRef)
from redux.types import int_, float_, object_, str_, is_numeric, common_arithmetic_type

import re

class IntrinsicFunction(object):
    @property
    def nontrivial(self):
        return False

    @property
    def name(self):
        return _convert(self.__class__.__name__)


class Say(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) > 0

        code_generator.emit("say ")
        code_generator.visit(args[0])
        for arg in args[1:]:
            code_generator.emit(", ")
            code_generator.visit(arg)

    def type(self, args):
        return None


class SetSayTarget(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 1
        assert args[0].type == str_

        code_generator.emit("(say_to_var")
        code_generator.visit(args[0])
        code_generator.emit(")")

    def type(self, args):
        return None


class SayConfigVar(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 1
        assert args[0].type == str_

        code_generator.emit("(say_from_config")
        code_generator.visit(args[0])
        code_generator.emit(")")

    def type(self, args):
        return None


def _unary_numeric_intrinsic(name, op, type_):
    class _Intrinsic(IntrinsicFunction):
        def codegen(self, code_generator, args):
            assert len(args) == 1
            assert is_numeric(args[0].type)

            code_generator.emit("(" + op + " ")
            code_generator.visit(args[0])
            code_generator.emit(")")

        def type(self, args):
            return type_
    _Intrinsic.__name__ = name
    return _Intrinsic

Sqrt = _unary_numeric_intrinsic("Sqrt", "|/", float_)
Int = _unary_numeric_intrinsic("Int", "trunc", int_)
Float = _unary_numeric_intrinsic("Float", "to_float", float_)
Abs = _unary_numeric_intrinsic("Abs", "abs", float_)
Sin = _unary_numeric_intrinsic("Sin", "sin", float_)
Cos = _unary_numeric_intrinsic("Cos", "cos", float_)
Tan = _unary_numeric_intrinsic("Tan", "tan", float_)
Log = _unary_numeric_intrinsic("Log", "log", float_)
Asin = _unary_numeric_intrinsic("Asin", "asin", float_)
Acos = _unary_numeric_intrinsic("Acos", "acos", float_)
Rad2Rot = _unary_numeric_intrinsic("Rad2Rot", "radtorot", int_)
Rot2Rad = _unary_numeric_intrinsic("Rot2Rad", "rottorad", float_)

Rad2Rot.name = "rad2rot"
Rot2Rad.name = "rot2rad"

class Object(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 1
        assert args[0].type == int_

        code_generator.emit("(to_object ")
        code_generator.visit(args[0])
        code_generator.emit(")")

    def type(self, args):
        return object_

class Atan2(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 2
        assert is_numeric(args[0].type)
        assert is_numeric(args[1].type)

        code_generator.emit("(")
        code_generator.visit(args[0])
        code_generator.emit(" atan2 ")
        code_generator.visit(args[1])
        code_generator.emit(")")

    def type(self, args):
        return float_

class Max(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 2
        assert is_numeric(args[0].type)
        assert is_numeric(args[1].type)

        code_generator.emit("(")
        code_generator.visit(args[0])
        code_generator.emit("|>")
        code_generator.visit(args[1])
        code_generator.emit(")")

    def type(self, args):
        return common_arithmetic_type(args[0].type, args[1].type)

class Min(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 2
        assert is_numeric(args[0].type)
        assert is_numeric(args[1].type)

        code_generator.emit("(")
        code_generator.visit(args[0])
        code_generator.emit("<|")
        code_generator.visit(args[1])
        code_generator.emit(")")

    def type(self, args):
        return common_arithmetic_type(args[0].type, args[1].type)


class DistSq(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 2
        assert args[0].type == object_
        assert args[1].type == object_

        code_generator.emit("(")
        code_generator.visit(args[0])
        code_generator.emit("<=>")
        code_generator.visit(args[1])
        code_generator.emit(")")

    def type(self, args):
        return float_

class HDistSq(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 2
        assert args[0].type == object_
        assert args[1].type == object_

        code_generator.emit("(")
        code_generator.visit(args[0])
        code_generator.emit("<_>")
        code_generator.visit(args[1])
        code_generator.emit(")")

    def type(self, args):
        return float_

    @property
    def name(self):
        return "hdist_sq"


class VDistSq(IntrinsicFunction):
    def codegen(self, code_generator, args):
        assert len(args) == 2
        assert args[0].type == object_
        assert args[1].type == object_

        code_generator.emit("(")
        code_generator.visit(args[0])
        code_generator.emit("<^>")
        code_generator.visit(args[1])
        code_generator.emit(")")

    def type(self, args):
        return float_

    @property
    def name(self):
        return "vdist_sq"


GetAchronalField = lambda: FunctionDefinition("__get_achronal_field", ["num"], Block([CodeLiteral("PERFORM GET_ACHRONAL_FIELD num;"), ReturnStmt(VarRef("perf_ret"))]))
SetAchronalField = lambda: FunctionDefinition("__set_achronal_field", ["num", "value"], Block([CodeLiteral("target = num; PERFORM SET_ACHRONAL_FIELD value;")]))

# From http://stackoverflow.com/a/1176023/126977
def _convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def get_intrinsic_functions():
    for cls in IntrinsicFunction.__subclasses__():
        intrinsic = cls()
        yield intrinsic.name, intrinsic
