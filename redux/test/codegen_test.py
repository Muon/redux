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
        ("a = 1 | 1", "int a = (1|1);"),
        ("a = 1 ^ 1", "int a = (1^1);"),
        ("a = 1 & 1", "int a = (1&1);"),
        ("a = 1 >> 1", "int a = (1>>1);"),
        ("a = 1 << 1", "int a = (1<<1);"),
        ("a = 1 ** 1", "int a = (1**1);"),
        ("a = ~1", "int a = (~1);"),
        ("a = 1 % 1", "int a = (1%1);"),
        ("a = 1 b = -a", "int a = 1;\nint b = (-a);"),
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
        ("say(unit.Length)", "say (unit.Length);"),
        ("say(1::Rank)", "say (1::Rank);"),
        ("a = (QUERY UNIT WHERE query->HP > 0)", "object a = (QUERY UNIT [unit] MIN [1] WHERE [((query->HP)>0)]);"),
        ("a = (QUERY VALUE MIN query->HP)", "int a = (QUERY VALUE [unit] MIN [(query->HP)] WHERE [1]);"),
        ("def f() a = 1 end a = 2 f()", "int a = 2;\n{\nint a = 1;\n}"),
        ("for a = 1, a < 100, a = a + 1 say(a) end", "for(int a = 1; (a<100); a = (a+1)){\nsay a;\n}"),
        ("def f(x) return x*x end for a = f(2), a < f(8), a = a + 1 end", "int __retval1 = 0;\n{\nint x = 2;\n__retval1 = (x*x);\n}\nfor(int a = __retval1; ; a = (a+1)){\nint __retval0 = 0;\n{\nint x = 8;\n__retval0 = (x*x);\n}\nif((a<__retval0)){\n}\nelse {\nbreak;\n}\n}"),
        ("def f(x) return x*x end for a = 1, a < 100, a = f(a) end", "for(int a = 1; (a<100); ){\n{\n}\nint __retval0 = 0;\n{\nint x = a;\n__retval0 = (x*x);\n}\na = __retval0;\n}"),
        ("a = rad2rot(0)", "int a = (radtorot0);"),
        ("a = rot2rad(0)", "float a = (rottorad0);"),
        ("a = sin(0)", "float a = (sin0);"),
        ("a = cos(0)", "float a = (cos0);"),
        ("a = tan(0)", "float a = (tan0);"),
        ("a = asin(0)", "float a = (asin0);"),
        ("a = acos(0)", "float a = (acos0);"),
        ("a = atan2(0, 0)", "float a = (0atan20);"),
        ("a = log(1)", "float a = (log1);"),
        ("a = object(0)", "object a = (to_object0);"),
        ("a = int(0)", "int a = (trunc0);"),
        ("a = float(0)", "float a = (to_float0);"),
        ("a = dist_sq(unit, unit)", "float a = (unit<=>unit);"),
        ("a = hdist_sq(unit, unit)", "float a = (unit<_>unit);"),
        ("a = vdist_sq(unit, unit)", "float a = (unit<^>unit);"),
        ("a = max(1, 2)", "int a = (1|>2);"),
        ("a = max(1.0, 2.0)", "float a = (1.0|>2.0);"),
        ("a = min(1, 2)", "int a = (1<|2);"),
        ("a = min(1.0, 2.0)", "float a = (1.0<|2.0);"),
        ("set_say_target(\"foo\")", "(say_to_var\"foo\");"),
        ("say_config_var(\"foo\")", "(say_from_config\"foo\");"),
        ("target = object(0)", "target = (to_object0);"),
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


@raises(IncompatibleTypeError)
def test_assign_to_bitfield_def():
    c("bitfield A x : 1 end A = 1")


@raises(IncompatibleTypeError)
def test_assign_to_func_def():
    c("def f() end f = 1")
