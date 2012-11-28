from redux.ast import Constant
from redux.types import int_
from redux.visitor import ASTTransformer


class EnumInliner(ASTTransformer):
    """Inlines all enum constants."""
    def __init__(self):
        super(ASTTransformer, self).__init__()
        self.scopes = []

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def find_enum_constant(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise KeyError(name)

    def visit_VarRef(self, var_ref):
        try:
            return self.find_enum_constant(var_ref.name)
        except KeyError:
            return var_ref

    def visit_EnumDefinition(self, enum_def):
        self.generic_visit(enum_def)

        for name, value in enum_def.members:
            self.scopes[-1][name] = Constant(value, int_)

        return enum_def
