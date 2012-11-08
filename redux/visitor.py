class Visitor(object):
    "Implements the extrinsic Visitor pattern."

    def visit(self, node, *args, **kwargs):
        "Starts visiting node."
        for cls in node.__class__.__mro__:
            meth_name = 'visit_' + cls.__name__
            meth = getattr(self, meth_name, None)
            if meth:
                return meth(node, *args, **kwargs)

        return self.generic_visit(node, *args, **kwargs)


class ASTVisitor(Visitor):
    def push_scope(self):
        pass

    def pop_scope(self):
        pass

    def generic_visit(self, node):
        raise RuntimeError("non-AST node object %r visited" % node)

    def visit_ASTNode(self, node):
        assert False, "unhandled node in AST visitor: %r" % node

    def visit_Block(self, block):
        self.push_scope()

        for statement in block.statements:
            self.visit(statement)

        self.pop_scope()

        return block

    def visit_Assignment(self, assignment):
        self.visit(assignment.expression)
        return assignment

    def visit_FunctionCall(self, func_call):
        for argument in func_call.arguments:
            self.visit(argument)

        return func_call

    def visit_FunctionDefinition(self, func_def):
        return func_def

    def visit_BitfieldDefinition(self, bitfield_def):
        return bitfield_def

    def visit_EnumDefinition(self, enum_def):
        return enum_def

    def visit_BitfieldAccess(self, bitfield_access):
        return bitfield_access

    def visit_IfStmt(self, if_stmt):
        self.visit(if_stmt.condition)
        self.visit(if_stmt.then_block)

        if if_stmt.else_part:
            self.visit(if_stmt.else_part)

        return if_stmt

    def visit_BreakStmt(self, break_stmt):
        return break_stmt

    def visit_VarRef(self, var_ref):
        return var_ref

    def visit_WhileStmt(self, while_stmt):
        self.visit(while_stmt.condition)
        self.visit(while_stmt.block)

        return while_stmt

    def visit_ReturnStatement(self, return_stmt):
        self.visit(return_stmt.expression)

        return return_stmt

    def visit_Constant(self, constant):
        return constant

    def visit_BinaryOp(self, node):
        self.visit(node.lhs)
        self.visit(node.rhs)

        return node

    def visit_LogicalNotOp(self, node):
        self.visit(node.expression)

        return node

    def visit_CodeLiteral(self, code_literal):
        return code_literal
