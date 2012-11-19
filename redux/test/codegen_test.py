from nose.tools import eq_, raises
from redux.codegenerator import compile_script
from redux.typeannotate import UndefinedVariableError, InvalidExpressionError, NotCallableError, IncompatibleTypeError, UndefinedTypeError, ImmutabilityViolationError


def c(code):
    return compile_script("codegen_test", code)


def test_code_generation():
    code_examples = [
        ("if 2 > 1 else end", "if((2>1)){\n}\nelse {\n}"),
        ("while 2 > 1 end", "while(1){\nif((2>1)){\n}\nelse {\nbreak;\n}\n}"),
        ("def f(a) return a end x = f(1)", "int __retval0 = 0;\n{\nint a = 1;\n__retval0 = a;\n}\nint x = __retval0;"),
        ("say(1, 2)", "say 1, 2;"),
        ("sqrt(2)", "(|/2);"),
        ("a = sqrt(2)", "float a = (|/2);"),
        ("`PERFORM RAND;` a = perf_ret", "PERFORM RAND;int a = perf_ret;"),
        ("a = \"foo\" say(a)", "say \"foo\";"),
        ("a = 1 - 1", "int a = (1-1);"),
        ("a = 1 + 1", "int a = (1+1);"),
        ("a = 1 * 1", "int a = (1*1);"),
        ("a = 1 / 1", "int a = (1/1);"),
        ("a = 1 > 1", "int a = (1>1);"),
        ("a = 1 < 1", "int a = (1<1);"),
        ("a = 1 <= 1", "int a = (1<=1);"),
        ("a = 1 >= 1", "int a = (1>=1);"),
        ("a = 1 == 1", "int a = (1==1);"),
        ("a = 1 != 1", "int a = (1!=1);"),
        ("a = 1 and 1", "int a = (1&&1);"),
        ("a = 1 or 1", "int a = (1||1);"),
        ("a = not 1", "int a = (!1);"),
        ("a = 1.0 b = 1 + a", "float a = 1.0;\nfloat b = (1+a);"),
        ("a = 1 b = 1.0 a = b", "int a = 1;\nfloat b = 1.0;\na = b;"),
        ("bitfield A x : 12 y : 12 z : 8 end a = A(0)", "int a = 0;"),
        ("bitfield A x : 12 y : 12 z : 8 end a = A(0) a.x = 1", "int a = 0;\na[0, 12] = 1;"),
        ("bitfield A x : 12 y : 12 z : 8 end a = A(0) b = a.y", "int a = 0;\nint b = a[12, 12];"),
        ("enum A a b c d end x = a", "int x = 0;"),
        ("AF[0] = 1", "{\nint num = 0;\nint value = 1;\ntarget = num; PERFORM SET_ACHRONAL_FIELD value;}"),
        ("a = AF[0]", "int __retval0 = 0;\n{\nint num = 0;\nPERFORM GET_ACHRONAL_FIELD num;__retval0 = perf_ret;\n}\nint a = __retval0;"),
        ("def f() return sqrt(1) end f()", "float __retval0 = 0;\n{\n__retval0 = (|/1);\n}\n__retval0;"),
        ("say(unit->Timestamp)", "say (unit->Timestamp);"),
    ]

    for redux_code, rescript_code in code_examples:
        yield check_code_generation, redux_code, ("{\n" + rescript_code + "\n}\n")


def check_code_generation(redux_code, rescript_code):
    eq_(c(redux_code), rescript_code)


@raises(UndefinedVariableError)
def test_undefined_var_use():
    c("say(a)")


@raises(UndefinedVariableError)
def test_undefined_var_assign():
    c("a = x")


@raises(InvalidExpressionError)
def test_incompatible_add():
    c('a = "abc" + "abc"')


@raises(NotCallableError)
def test_invalid_cast_to_bitfield():
    c("x = 1 x(0)")


@raises(IncompatibleTypeError)
def test_invalid_bitfield_assign_type():
    c("bitfield A x : 1 end a = A(0) a.x = 1.0")


@raises(UndefinedTypeError)
def test_assign_returnless_function():
    c("def f() end a = f()")


@raises(ImmutabilityViolationError)
def test_attempt_modify_enum():
    c("enum A x y z end x = 1")


@raises(IncompatibleTypeError)
def test_modify_string():
    c('a = "abc" a = "def"')


@raises(IncompatibleTypeError)
def test_assign_string_to_numeric():
    c('a = 1 a = "abc"')


@raises(IncompatibleTypeError)
def test_assign_bitfield_to_numeric():
    c("bitfield A x : 12 end a = 1 a = A(0)")


@raises(InvalidExpressionError)
def test_call_with_wrong_arg_count():
    c("def f(a, b) end f(1)")
