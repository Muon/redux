import sys
from redux.assignmentdeclare import AssignmentScopeAnalyzer
from redux.ast import BitfieldDefinition
from redux.callinliner import CallInliner
from redux.enuminliner import EnumInliner
from redux.intrinsics import SayFunction, SqrtFunction
from redux.parser import parse
from redux.stringinliner import StringInliner
from redux.typeannotate import TypeAnnotator
from redux.types import str_, float_, int_, object_, is_numeric
from redux.visitor import ASTVisitor


class CodeGenerator(ASTVisitor):
    """Generates code from AST."""
    def __init__(self):
        super(CodeGenerator, self).__init__()
        self.intrinsics = {"say": SayFunction(), "sqrt": SqrtFunction()}

        self.code = ""

    def emit(self, new_code):
        self.code += new_code

    def push_scope(self):
        self.emit("{\n")

    def pop_scope(self):
        self.emit("}\n")

    def type_name(self, type_):
        if isinstance(type_, BitfieldDefinition):
            type_ = int_

        return {int_: "int", float_: "float", object_: "object"}[type_]

    def visit_Constant(self, constant):
        if is_numeric(constant.type):
            self.emit(repr(constant.value))
        elif constant.type is str_:
            self.emit('"%s"' % constant.value.encode("unicode_escape").decode("utf8").replace('"', '\"'))
        else:
            assert False, "constant of unknown type %r" % constant.type

    def visit_FunctionCall(self, func_call):
        if isinstance(func_call.type, BitfieldDefinition):
            self.visit(func_call.arguments[0])
        else:
            self.intrinsics[func_call.function].codegen(self, func_call.arguments)

    def visit_VarRef(self, var_ref):
        self.emit(var_ref.name)

    def emit_binary_op(self, binop, op):
        self.emit("(")
        self.visit(binop.lhs)
        self.emit(op)
        self.visit(binop.rhs)
        self.emit(")")

    def emit_unary_op(self, unop, op):
        self.emit("(")
        self.emit(op)
        self.visit(unop.expression)
        self.emit(")")

    def visit_AddOp(self, binop):
        self.emit_binary_op(binop, "+")

    def visit_SubOp(self, binop):
        self.emit_binary_op(binop, "-")

    def visit_MulOp(self, binop):
        self.emit_binary_op(binop, "*")

    def visit_DivOp(self, binop):
        self.emit_binary_op(binop, "/")

    def visit_LessThanOp(self, binop):
        self.emit_binary_op(binop, "<")

    def visit_GreaterThanOp(self, binop):
        self.emit_binary_op(binop, ">")

    def visit_LessThanOrEqualToOp(self, binop):
        self.emit_binary_op(binop, "<=")

    def visit_GreaterThanOrEqualToOp(self, binop):
        self.emit_binary_op(binop, ">=")

    def visit_EqualToOp(self, binop):
        self.emit_binary_op(binop, "==")

    def visit_NotEqualToOp(self, binop):
        self.emit_binary_op(binop, "!=")

    def visit_LogicalAndOp(self, binop):
        self.emit_binary_op(binop, "&&")

    def visit_LogicalOrOp(self, binop):
        self.emit_binary_op(binop, "||")

    def visit_LogicalNotOp(self, a):
        self.emit_unary_op(a, "!")

    def visit_BitwiseOrOp(self, binop):
        self.emit_binary_op(binop, "|")

    def visit_BitwiseXorOp(self, binop):
        self.emit_binary_op(binop, "^")

    def visit_BitwiseAndOp(self, binop):
        self.emit_binary_op(binop, "&")

    def visit_BitwiseLeftShiftOp(self, binop):
        self.emit_binary_op(binop, "<<")

    def visit_BitwiseRightShiftOp(self, binop):
        self.emit_binary_op(binop, ">>")

    def visit_ModuloOp(self, binop):
        self.emit_binary_op(binop, "%")

    def visit_NegateOp(self, unop):
        self.emit_unary_op(unop, "-")

    def visit_BitfieldAssignment(self, assignment):
        self.visit(assignment.variable)
        self.emit(" = ")
        self.visit(assignment.expression)

    def visit_Assignment(self, assignment):
        if assignment.declare is True:
            self.emit("%s " % self.type_name(assignment.variable.type))

        self.visit(assignment.variable)
        self.emit(" = ")
        self.visit(assignment.expression)

    def visit_DottedAccess(self, dotted_access):
        if dotted_access.expression.type == object_:
            self.emit("(")
            self.visit(dotted_access.expression)
            self.emit(".%s)" % dotted_access.member)
        else:
            self.visit(dotted_access.expression)
            self.emit("[%d, %d]" % dotted_access.expression.type.get_member_limits(dotted_access.member))

    def visit_Block(self, block):
        self.push_scope()

        for statement in block.statements:
            old_length = len(self.code)
            self.visit(statement)
            if old_length < len(self.code) and self.code[-1] != ";" and self.code[-2:] != "}\n":
                self.emit(";\n")

        self.pop_scope()

    def visit_IfStmt(self, if_stmt):
        self.emit("if(")
        self.visit(if_stmt.condition)
        self.emit(")")
        self.visit(if_stmt.then_block)
        if if_stmt.else_part is not None:
            self.emit("else ")
            self.visit(if_stmt.else_part)

    def visit_WhileStmt(self, while_stmt):
        self.emit("while(")
        self.visit(while_stmt.condition)
        self.emit(")")
        self.visit(while_stmt.block)

    def visit_CodeLiteral(self, code_literal):
        self.emit(code_literal.code)

    def visit_BreakStmt(self, break_stmt):
        self.emit("break")

    def visit_ChronalAccess(self, chronal_access):
        self.emit("(")
        self.visit(chronal_access.object)
        self.emit("->%s)" % chronal_access.member)

    def visit_ClassAccess(self, class_access):
        self.emit("(")
        self.visit(class_access.class_)
        self.emit("::%s)" % class_access.member)

    def visit_Query(self, query):
        self.emit("(")
        self.emit("QUERY %s [" % query.query_type)
        self.visit(query.unit)
        self.emit("] %s [" % query.op)
        self.visit(query.op_expr)
        self.emit("] WHERE [")
        self.visit(query.where_cond)
        self.emit("])")


def compile_script(filename, code):
    code_generator = CodeGenerator()
    ast_, errors = parse(code)
    for lineno, message in errors:
        sys.stderr.write("%s:%d: %s\n" % (filename, lineno, message))

    ast_ = AssignmentScopeAnalyzer().visit(ast_)
    ast_ = TypeAnnotator().visit(ast_)
    ast_ = CallInliner().visit(ast_)
    ast_ = EnumInliner().visit(ast_)
    ast_ = StringInliner().visit(ast_)

    code_generator.visit(ast_)

    return code_generator.code
