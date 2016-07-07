"""
Cretonne base instruction set.

This module defines the basic Cretonne instruction set that all targets
support.
"""
from . import TypeVar, Operand, Instruction, InstructionGroup, variable_args
from types import i8, f32, f64
from immediates import imm64, uimm8, ieee32, ieee64, immvector, intcc, floatcc
import entities

instructions = InstructionGroup("base", "Shared base instruction set")

Int = TypeVar('Int', 'A scalar or vector integer type', ints=True, simd=True)
iB = TypeVar('iB', 'A scalar integer type', ints=True)
Testable = TypeVar(
        'Testable', 'A scalar boolean or integer type',
        ints=True, bools=True)
TxN = TypeVar(
        'TxN', 'A SIMD vector type',
        ints=True, floats=True, bools=True, scalars=False, simd=True)
Any = TypeVar(
        'Any', 'Any integer, float, or boolean scalar or vector type',
        ints=True, floats=True, bools=True, scalars=True, simd=True)

#
# Control flow
#
c = Operand('c', Testable, doc='Controlling value to test')
EBB = Operand('EBB', entities.ebb, doc='Destination extended basic block')
args = Operand('args', variable_args, doc='EBB arguments')

jump = Instruction(
        'jump', r"""
        Jump.

        Unconditionally jump to an extended basic block, passing the specified
        EBB arguments. The number and types of arguments must match the
        destination EBB.
        """,
        ins=(EBB, args), is_terminator=True)

brz = Instruction(
        'brz', r"""
        Branch when zero.

        If ``c`` is a :type:`b1` value, take the branch when ``c`` is false. If
        ``c`` is an integer value, take the branch when ``c = 0``.
        """,
        ins=(c, EBB, args), is_branch=True)

brnz = Instruction(
        'brnz', r"""
        Branch when non-zero.

        If ``c`` is a :type:`b1` value, take the branch when ``c`` is true. If
        ``c`` is an integer value, take the branch when ``c != 0``.
        """,
        ins=(c, EBB, args), is_branch=True)

x = Operand('x', iB, doc='index into jump table')
JT = Operand('JT', entities.jump_table)
br_table = Instruction(
        'br_table', r"""
        Indirect branch via jump table.

        Use ``x`` as an unsigned index into the jump table ``JT``. If a jump
        table entry is found, branch to the corresponding EBB. If no entry was
        found fall through to the next instruction.

        Note that this branch instruction can't pass arguments to the targeted
        blocks. Split critical edges as needed to work around this.
        """,
        ins=(x, JT), is_branch=True)

trap = Instruction(
        'trap', r"""
        Terminate execution unconditionally.
        """,
        is_terminator=True)

trapz = Instruction(
        'trapz', r"""
        Trap when zero.

        if ``c`` is non-zero, execution continues at the following instruction.
        """,
        ins=c)

trapnz = Instruction(
        'trapnz', r"""
        Trap when non-zero.

        if ``c`` is zero, execution continues at the following instruction.
        """,
        ins=c)

#
# Materializing constants.
#

N = Operand('N', imm64)
a = Operand('a', Int, doc='A constant integer scalar or vector value')
iconst = Instruction(
        'iconst', r"""
        Integer constant.

        Create a scalar integer SSA value with an immediate constant value, or
        an integer vector where all the lanes have the same value.
        """,
        ins=N, outs=a)

N = Operand('N', ieee32)
a = Operand('a', f32, doc='A constant integer scalar or vector value')
f32const = Instruction(
        'f32const', r"""
        Floating point constant.

        Create a :type:`f32` SSA value with an immediate constant value, or a
        floating point vector where all the lanes have the same value.
        """,
        ins=N, outs=a)

N = Operand('N', ieee64)
a = Operand('a', f64, doc='A constant integer scalar or vector value')
f64const = Instruction(
        'f64const', r"""
        Floating point constant.

        Create a :type:`f64` SSA value with an immediate constant value, or a
        floating point vector where all the lanes have the same value.
        """,
        ins=N, outs=a)

N = Operand('N', immvector)
a = Operand('a', TxN, doc='A constant vector value')
vconst = Instruction(
        'vconst', r"""
        Vector constant (floating point or integer).

        Create a SIMD vector value where the lanes don't have to be identical.
        """,
        ins=N, outs=a)

#
# Generics.
#

c = Operand('c', Testable, doc='Controlling value to test')
x = Operand('x', Any, doc='Value to use when `c` is true')
y = Operand('y', Any, doc='Value to use when `c` is false')
a = Operand('a', Any)

select = Instruction(
        'select', r"""
        Conditional select.

        This instruction selects whole values. Use :inst:`vselect` for
        lane-wise selection.
        """,
        ins=(c, x, y), outs=a)

#
# Vector operations
#

c = Operand('c', TxN.as_bool(), doc='Controlling vector')
x = Operand('x', TxN, doc='Value to use where `c` is true')
y = Operand('y', TxN, doc='Value to use where `c` is false')
a = Operand('a', TxN)

vselect = Instruction(
        'vselect', r"""
        Vector lane select.

        Select lanes from ``x`` or ``y`` controlled by the lanes of the boolean
        vector ``c``.
        """,
        ins=(c, x, y), outs=a)

x = Operand('x', TxN.lane_of())

splat = Instruction(
        'splat', r"""
        Vector splat.

        Return a vector whose lanes are all ``x``.
        """,
        ins=x, outs=a)

x = Operand('x', TxN, doc='SIMD vector to modify')
y = Operand('y', TxN.lane_of(), doc='New lane value')
Idx = Operand('Idx', uimm8, doc='Lane index')

insertlane = Instruction(
        'insertlane', r"""
        Insert ``y`` as lane ``Idx`` in x.

        The lane index, ``Idx``, is an immediate value, not an SSA value. It
        must indicate a valid lane index for the type of ``x``.
        """,
        ins=(x, Idx, y), outs=a)

x = Operand('x', TxN)
a = Operand('a', TxN.lane_of())

extractlane = Instruction(
        'extractlane', r"""
        Extract lane ``Idx`` from ``x``.

        The lane index, ``Idx``, is an immediate value, not an SSA value. It
        must indicate a valid lane index for the type of ``x``.
        """,
        ins=(x, Idx), outs=a)

#
# Integer arithmetic
#

a = Operand('a', Int.as_bool())
Cond = Operand('Cond', intcc)
x = Operand('x', Int)
y = Operand('y', Int)

icmp = Instruction(
        'icmp', r"""
        Integer comparison.

        The condition code determines if the operands are interpreted as signed
        or unsigned integers.

        ====== ======== =========
        Signed Unsigned Condition
        ====== ======== =========
        eq     eq       Equal
        ne     ne       Not equal
        slt    ult      Less than
        sge    uge      Greater than or equal
        sgt    ugt      Greater than
        sle    ule      Less than or equal
        ====== ======== =========

        When this instruction compares integer vectors, it returns a boolean
        vector of lane-wise comparisons.
        """,
        ins=(Cond, x, y), outs=a)

a = Operand('a', Int)
x = Operand('x', Int)
y = Operand('y', Int)

iadd = Instruction(
        'iadd', r"""
        Wrapping integer addition: :math:`a := x + y \pmod{2^B}`.

        This instruction does not depend on the signed/unsigned interpretation
        of the operands.
        """,
        ins=(x, y), outs=a)

isub = Instruction(
        'isub', r"""
        Wrapping integer subtraction: :math:`a := x - y \pmod{2^B}`.

        This instruction does not depend on the signed/unsigned interpretation
        of the operands.
        """,
        ins=(x, y), outs=a)

imul = Instruction(
        'imul', r"""
        Wrapping integer multiplication: :math:`a := x y \pmod{2^B}`.

        This instruction does not depend on the signed/unsigned interpretation
        of the
        operands.

        Polymorphic over all integer types (vector and scalar).
        """,
        ins=(x, y), outs=a)

udiv = Instruction(
        'udiv', r"""
        Unsigned integer division: :math:`a := \lfloor {x \over y} \rfloor`.

        This operation traps if the divisor is zero.
        """,
        ins=(x, y), outs=a)

sdiv = Instruction(
        'sdiv', r"""
        Signed integer division rounded toward zero: :math:`a := sign(xy)
        \lfloor {|x| \over |y|}\rfloor`.

        This operation traps if the divisor is zero, or if the result is not
        representable in :math:`B` bits two's complement. This only happens
        when :math:`x = -2^{B-1}, y = -1`.
        """,
        ins=(x, y), outs=a)

urem = Instruction(
        'urem', """
        Unsigned integer remainder.

        This operation traps if the divisor is zero.
        """,
        ins=(x, y), outs=a)

srem = Instruction(
        'srem', """
        Signed integer remainder.

        This operation traps if the divisor is zero.

        .. todo:: Integer remainder vs modulus.

        Clarify whether the result has the sign of the divisor or the dividend.
        Should we add a ``smod`` instruction for the case where the result has
        the same sign as the divisor?
        """,
        ins=(x, y), outs=a)

a = Operand('a', iB)
x = Operand('x', iB)
Y = Operand('Y', imm64)

iadd_imm = Instruction(
        'iadd_imm', """
        Add immediate integer.

        Same as :inst:`iadd`, but one operand is an immediate constant.

        Polymorphic over all scalar integer types, but does not support vector
        types.
        """,
        ins=(x, Y), outs=a)

imul_imm = Instruction(
        'imul_imm', """
        Integer multiplication by immediate constant.

        Polymorphic over all scalar integer types.
        """,
        ins=(x, Y), outs=a)

udiv_imm = Instruction(
        'udiv_imm', """
        Unsigned integer division by an immediate constant.

        This instruction never traps because a divisor of zero is not allowed.
        """,
        ins=(x, Y), outs=a)

sdiv_imm = Instruction(
        'sdiv_imm', """
        Signed integer division by an immediate constant.

        This instruction never traps because a divisor of -1 or 0 is not
        allowed. """,
        ins=(x, Y), outs=a)

urem_imm = Instruction(
        'urem_imm', """
        Unsigned integer remainder with immediate divisor.

        This instruction never traps because a divisor of zero is not allowed.
        """,
        ins=(x, Y), outs=a)

srem_imm = Instruction(
        'srem_imm', """
        Signed integer remainder with immediate divisor.

        This instruction never traps because a divisor of 0 or -1 is not
        allowed. """,
        ins=(x, Y), outs=a)

# Swap x and y for isub_imm.
X = Operand('X', imm64)
y = Operand('y', iB)

isub_imm = Instruction(
        'isub_imm', """
        Immediate wrapping subtraction: :math:`a := X - y \pmod{2^B}`.

        Also works as integer negation when :math:`X = 0`. Use :inst:`iadd_imm`
        with a negative immediate operand for the reverse immediate
        subtraction.

        Polymorphic over all scalar integer types, but does not support vector
        types.
        """,
        ins=(X, y), outs=a)

#
# Bitwise operations.
#

# TODO: Which types should permit boolean operations? Any reason to restrict?
bits = TypeVar(
        'bits', 'Any integer, float, or boolean scalar or vector type',
        ints=True, floats=True, bools=True, scalars=True, simd=True)

x = Operand('x', bits)
y = Operand('y', bits)
a = Operand('a', bits)

band = Instruction(
        'band', """
        Bitwise and.
        """,
        ins=(x, y), outs=a)

bor = Instruction(
        'bor', """
        Bitwise or.
        """,
        ins=(x, y), outs=a)

bxor = Instruction(
        'bxor', """
        Bitwise xor.
        """,
        ins=(x, y), outs=a)

bnot = Instruction(
        'bnot', """
        Bitwise not.
        """,
        ins=x, outs=a)

# Shift/rotate.
x = Operand('x', Int, doc='Scalar or vector value to shift')
y = Operand('y', iB, doc='Number of bits to shift')
a = Operand('a', Int)

rotl = Instruction(
        'rotl', r"""
        Rotate left.

        Rotate the bits in ``x`` by ``y`` places.
        """,
        ins=(x, y), outs=a)

rotr = Instruction(
        'rotr', r"""
        Rotate right.

        Rotate the bits in ``x`` by ``y`` places.
        """,
        ins=(x, y), outs=a)

ishl = Instruction(
        'ishl', r"""
        Integer shift left. Shift the bits in ``x`` towards the MSB by ``y``
        places. Shift in zero bits to the LSB.

        The shift amount is masked to the size of ``x``.

        When shifting a B-bits integer type, this instruction computes:

        .. math::
            s &:= y \pmod B,                \\
            a &:= x \cdot 2^s \pmod{2^B}.

        .. todo:: Add ``ishl_imm`` variant with an immediate ``y``.

        """,
        ins=(x, y), outs=a)

ushr = Instruction(
        'ushr', r"""
        Unsigned shift right. Shift bits in ``x`` towards the LSB by ``y``
        places, shifting in zero bits to the MSB. Also called a *logical
        shift*.

        The shift amount is masked to the size of the register.

        When shifting a B-bits integer type, this instruction computes:

        .. math::
            s &:= y \pmod B,                \\
            a &:= \lfloor x \cdot 2^{-s} \rfloor.

        .. todo:: Add ``ushr_imm`` variant with an immediate ``y``.
        """,
        ins=(x, y), outs=a)

sshr = Instruction(
        'sshr', r"""
        Signed shift right. Shift bits in ``x`` towards the LSB by ``y``
        places, shifting in sign bits to the MSB. Also called an *arithmetic
        shift*.

        The shift amount is masked to the size of the register.

        .. todo:: Add ``sshr_imm`` variant with an immediate ``y``.
        """,
        ins=(x, y), outs=a)

#
# Bit counting.
#

x = Operand('x', iB)
a = Operand('a', i8)

clz = Instruction(
        'clz', r"""
        Count leading zero bits.

        Starting from the MSB in ``x``, count the number of zero bits before
        reaching the first one bit. When ``x`` is zero, returns the size of x
        in bits.
        """,
        ins=x, outs=a)

cls = Instruction(
        'cls', r"""
        Count leading sign bits.

        Starting from the MSB after the sign bit in ``x``, count the number of
        consecutive bits identical to the sign bit. When ``x`` is 0 or -1,
        returns one less than the size of x in bits.
        """,
        ins=x, outs=a)

ctz = Instruction(
        'ctz', r"""
        Count trailing zeros.

        Starting from the LSB in ``x``, count the number of zero bits before
        reaching the first one bit. When ``x`` is zero, returns the size of x
        in bits.
        """,
        ins=x, outs=a)

popcnt = Instruction(
        'popcnt', r"""
        Population count

        Count the number of one bits in ``x``.
        """,
        ins=x, outs=a)

#
# Floating point.
#

Float = TypeVar(
        'Float', 'A scalar or vector floating point type type',
        floats=True, simd=True)

Cond = Operand('Cond', floatcc)
x = Operand('x', Float)
y = Operand('y', Float)
a = Operand('a', Float.as_bool())

fcmp = Instruction(
        'fcmp', r"""
        Floating point comparison.

        Two IEEE 754-2008 floating point numbers, `x` and `y`, relate to each
        other in exactly one of four ways:

        == ==========================================
        UN Unordered when one or both numbers is NaN.
        EQ When :math:`x = y`. (And :math:`0.0 = -0.0`).
        LT When :math:`x < y`.
        GT When :math:`x > y`.
        == ==========================================

        The 14 :type:`floatcc` condition codes each correspond to a subset of
        the four relations, except for the empty set which would always be
        false, and the full set which would always be true.

        The condition codes are divided into 7 'ordered' conditions which don't
        include UN, and 7 unordered conditions which all include UN.

        +-------+------------+---------+------------+-------------------------+
        |Ordered             |Unordered             |Condition                |
        +=======+============+=========+============+=========================+
        |ord    |EQ | LT | GT|uno      |UN          |NaNs absent / present.   |
        +-------+------------+---------+------------+-------------------------+
        |eq     |EQ          |ueq      |UN | EQ     |Equal                    |
        +-------+------------+---------+------------+-------------------------+
        |one    |LT | GT     |ne       |UN | LT | GT|Not equal                |
        +-------+------------+---------+------------+-------------------------+
        |lt     |LT          |ult      |UN | LT     |Less than                |
        +-------+------------+---------+------------+-------------------------+
        |le     |LT | EQ     |ule      |UN | LT | EQ|Less than or equal       |
        +-------+------------+---------+------------+-------------------------+
        |gt     |GT          |ugt      |UN | GT     |Greater than             |
        +-------+------------+---------+------------+-------------------------+
        |ge     |GT | EQ     |uge      |UN | GT | EQ|Greater than or equal    |
        +-------+------------+---------+------------+-------------------------+

        The standard C comparison operators, `<, <=, >, >=`, are all ordered,
        so they are false if either operand is NaN. The C equality operator,
        `==`, is ordered, and since inequality is defined as the logical
        inverse it is *unordered*. They map to the :type:`floatcc` condition
        codes as follows:

        ==== ====== ============
        C    `Cond` Subset
        ==== ====== ============
        `==` eq     EQ
        `!=` ne     UN | LT | GT
        `<`  lt     LT
        `<=` le     LT | EQ
        `>`  gt     GT
        `>=` ge     GT | EQ
        ==== ====== ============

        This subset of condition codes also corresponds to the WebAssembly
        floating point comparisons of the same name.

        When this instruction compares floating point vectors, it returns a
        boolean vector with the results of lane-wise comparisons.
        """,
        ins=(Cond, x, y), outs=a)

instructions.close()
