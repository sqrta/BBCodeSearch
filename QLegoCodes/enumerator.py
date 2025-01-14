import numpy as np
from numpy.polynomial import Polynomial
from numpy.polynomial.polynomial import polyval3d
from sympy import symbols, simplify, Poly
from sympy.core.add import Add
from sympy.abc import x, y, z, i, j
from code_def import *
from adt import *


def get_enum_tensor(code, indices):
    rank = len(indices)
    stab_group = stabilizer_group(code)
    max_degree = next(iter(stab_group)).length - rank
    pauli_map = {"I": 0, "X": 1, "Y": 2, "Z": 3}
    # enumerator = np.full([4]*rank, fill_value=Polynomial([0]*(max_degree+1)))
    enumerator = [0] if rank == 0 else np.full([4] * rank, fill_value=0, dtype=object)
    # print(f"stab length: {len(stab_group)}")
    for stab in stab_group:
        index = [pauli_map[stab.value[i].value] for i in indices]
        weight = stab.weight() - rank + index.count(0)
        wx = stab.W("X") - index.count(1)
        wy = stab.W("Y") - index.count(2)
        wz = stab.W("Z") - index.count(3)
        term = 1 if wx + wy + wz == 0 else x ** (wx) * y**wy * z**wz
        # term = 1 if wx+wy+wz==0 else x**(wx )* x**wy * x**wz
        index = 0 if rank == 0 else tuple(index)
        enumerator[index] += term
    return enumerator


def enum_error(code, Xvec, ZVec):
    indices = [0]
    rank = len(indices)
    stab_group = stabilizer_group(code)
    max_degree = next(iter(stab_group)).length - rank
    pauli_map = {"I": 0, "X": 1, "Y": 2, "Z": 3}
    # enumerator = np.full([4]*rank, fill_value=Polynomial([0]*(max_degree+1)))
    enumerator = [0] if rank == 0 else np.full([4] * rank, fill_value=0, dtype=object)
    # print(f"stab length: {len(stab_group)}")
    for stab in stab_group:
        index = [pauli_map[stab.value[i].value] for i in indices]
        weight = stab.weight() - rank + index.count(0)
        wx = stab.W("X") - index.count(1)
        wy = stab.W("Y") - index.count(2)
        wz = stab.W("Z") - index.count(3)
        term = 1 if wx + wy + wz == 0 else x ** (wx) * y**wy * z**wz
        # term = 1 if wx+wy+wz==0 else x**(wx )* x**wy * x**wz
        index = 0 if rank == 0 else tuple(index)
        enumerator[index] += term
    return enumerator


def get_BPoly(APoly, n, k):
    lx = symbols("lx")
    poly_coeff = simp_poly(APoly).all_coeffs()[-1::-1]
    poly = 0
    for i in range(len(poly_coeff)):
        lz = (1 - lx) / 2
        lw = (1 + 3 * lx) / 2
        poly += poly_coeff[i] * lz**i * lw ** (n - i)
    poly = Poly(simplify(2**k * poly))
    return poly.all_coeffs()[-1::-1]


def getK(APoly, n):
    lx = symbols("lx")
    poly_coeff = simp_poly(APoly).all_coeffs()[-1::-1]
    poly = 0
    for i in range(len(poly_coeff)):
        lz = (1 - lx) / 2
        lw = (1 + 3 * lx) / 2
        poly += poly_coeff[i] * lz**i * lw ** (n - i)
    poly = Poly(simplify(poly))
    return poly.all_coeffs()[-1]


def getKFromApoly(A_expr, n, k):
    Az_coeff = simp_poly(A_expr).all_coeffs()[-1::-1]
    Bz_coeff = get_BPoly(A_expr, n, k)
    K = int(Bz_coeff[0] / Az_coeff[0])
    return K


def K_from_poly(A_expr, n, k):
    Az_coeff = simp_poly(A_expr).all_coeffs()[-1::-1]
    Bz_coeff = get_BPoly(A_expr, n, k)

    # if True:
    #     print("A B", Az_coeff, Bz_coeff)
    return int(Bz_coeff[0] / Az_coeff[0])


def distance_from_poly(A_expr, n, k):
    Az_coeff = simp_poly(A_expr).all_coeffs()[-1::-1]
    Bz_coeff = get_BPoly(A_expr, n, k)

    if True:
        print("A B", Az_coeff, Bz_coeff)

    for d in range(len(Az_coeff)):
        if Az_coeff[d] != Bz_coeff[d]:
            return d


def AxzNoise(n, APoly, px, wx, pz, wz):
    return wx**n * wz**n * APoly.subs([(x, px / wx), (z, pz / wz)])


def BxzNoise(n, k, APoly, x, y, z, w):
    return 2**k * AxzNoise(n, APoly, w - z, z + w, (y - x) / 2, (x + y) / 2)


def simp_poly(enum_poly):
    try:
        return Poly(enum_poly.subs([(y, x), (z, x)]))
    except:
        return enum_poly


def normalize(poly):
    eff = poly.all_coeffs()[-1]
    return poly / eff


def xzNoise(n, k, APoly, px, pz):
    APoly = APoly.subs(y, x * z)
    A = AxzNoise(n, APoly, px, 1 - px, pz, 1 - pz)
    B = BxzNoise(n, k, APoly, px, 1 - px, pz, 1 - pz)
    K = getKFromApoly(APoly, n, k)
    # print(f"A: {A}, B: {B}")
    return B / K - A


def show2Dsimp(enumerator):
    for row in enumerator:
        for col in row:
            print(simp_poly(col))
        print("")


def parse(tn):
    program = copy.deepcopy(tn)
    insList = program.insList
    tnList = program.tensorList
    tnEnum = get_enum_tensor(tnList[0].tensor(), tnList[0].tracted)

    def getMIndex(traceIndex):
        return sum([len(t.tracted) for t in tnList[:traceIndex]])

    for ins in insList:
        if ins[0] == "trace":
            traceIndex, traceLeg, newOneIndex, newOneleg = ins[1:]
            matrixIndex = getMIndex(traceIndex)
            newOne = tnList[newOneIndex]
            newTensor = get_enum_tensor(newOne.tensor(), newOne.tracted)
            newTNindex = newOne.tracted.index(newOneleg)
            tmp = np.tensordot(tnEnum, newTensor, axes=[matrixIndex, newTNindex])
            tnEnum = tmp
            newOne.tracted.pop(0)
            tnList[traceIndex].tracted.pop(0)
        if ins[0] == "self":
            index1, leg1, index2, leg2 = ins[1:]
            mIndex1 = getMIndex(index1)
            mIndex2 = getMIndex(index2)
            # print(tnList[index1].tracted)
            # print(tnList[index2].tracted)
            # print(mIndex1, mIndex2)
            # print("shape",tnEnum.shape)
            tnEnum = np.trace(tnEnum, axis1=mIndex1, axis2=mIndex2)
            tnList[index1].tracted.pop(0)
            tnList[index2].tracted.pop(0)
    return tnEnum


def eval_code(stabilizers, k, px=0.01, pz=0.05):
    code = codeTN(stabilizers, isStab=True)
    n = code.length
    APoly = get_enum_tensor(code, [])[0]
    stab_group = stabilizer_group(stabilizers)
    K = K_from_poly(simp_poly(APoly), n, k)
    return ABzx(stab_group, px, 1 - px, pz, 1 - pz, k, K)[1]


def eval_tn(tn, px=0.01, pz=0.05):
    n = tn.get_n()
    k = tn.get_k()
    enum = parse(tn)
    APoly = enum.take(0)
    # print("APoly",Poly(APoly))
    simpA = simp_poly(APoly)
    print("simp", simpA)
    A1 = simpA.all_coeffs()[-1]
    d = distance_from_poly(simpA / A1, n, k)
    noise = xzNoise(n, k, APoly / A1, px, pz)
    return d, noise


def Poly2Distance(APoly, BPoly):
    A1 = APoly.all_coeffs()[-1]
    Az_coeff = [i / A1 for i in APoly.all_coeffs()[-1::-1]]
    B1 = BPoly.all_coeffs()[-1]
    Bz_coeff = [i / B1 for i in BPoly.all_coeffs()[-1::-1]]
    # print(Az_coeff,Bz_coeff)
    for d in range(len(Az_coeff)):
        if Az_coeff[d] != Bz_coeff[d]:
            return d


def ABError(n, APoly, BPoly, px, pz):
    wx = 1 - px
    wz = 1 - pz
    Azx = wx**n * wz**n * APoly.subs([(x, px / wx), (z, pz / wz)])
    Bzx = wx**n * wz**n * BPoly.subs([(x, px / wx), (z, pz / wz)])
    # print(f"Bzx: {Bzx}, Azx: {Azx}")
    pL = Bzx - Azx
    pnorm = 1 - Azx / Bzx
    # print(f"p_l: {pL:.5e}, pnorm: {pnorm:.5e}")
    return pnorm


def eval_TN(tn, px=0.01, pz=0.05):
    n = tn.get_n()
    k = tn.get_k()
    enum = parse(tn)
    try:
        APoly = enum.take(0)
        BPoly = np.sum(enum)
    except AttributeError:
        APoly = enum
        BPoly = enum

    tmp = simp_poly(BPoly)
    simpA = simp_poly(APoly)
    simpB = simp_poly(BPoly)
    A1 = simpA.all_coeffs()[-1]
    B1 = simpB.all_coeffs()[-1]

    APoly = APoly / A1
    BPoly = BPoly / B1

    K = B1 / A1
    d = Poly2Distance(simpA, simpB)
    error = ABError(n, APoly.subs([(y, x * z)]), BPoly.subs([(y, x * z)]), px, pz)
    if error == 0:
        error = 1
    return d, error, K


def prog2TNN(insList, tensorList):
    progList = []

    for state in insList:
        # ins = [state[0], state[1][0], state[1][1], state[1][0], state[1][1]]
        ins = state
        if ins[0] == "trace":
            index = ins[3]
            ins[3] = Tensor(tensorList[index])
        progList.append(ins)
    return buildProg(progList, Tensor(tensorList[0]))


if __name__ == "__main__":
    n = 5
    px = 0.01
    pz = 0.05
    code = code513
    code = code613
    print(get_enum_tensor(code513v, []))
    print(get_enum_tensor(code513, []))
    exit(0)
    d, error = eval_code(code, 1)
    cm = TNNetwork(Tensor("code513")).toCm()
    print(f"d: {d}, error: {error}, rowW: {cm.rowWBound()}, colW: {cm.colWBound()}")

    # tn = TNNetwork(Tensor(code603))
    # tn.trace(0, 0, Tensor(code603), 0)
    # tn.selfTrace(0,1,1,1)
    # tn.setLogical(0,2)

    # exit(0)
    # tn = TNNetwork(Tensor(code603, 6))
    # tn.trace(0, 2, Tensor(code603, 6), 0)
    # tn.trace(0, 3, Tensor(code603, 6), 0)
    # tn.trace(0, 4, Tensor(code603, 6), 0)
    # tn.trace(0, 5, Tensor(code603, 6), 0)
    # tn.setLogical(0,0)

    # n = tn.get_n()
    # k = tn.get_k()
    # print(n,k)
    # APoly = parse(tn)

    # print(APoly)
    # print(simp_poly(APoly))
    # print("d", distance_from_poly(simp_poly(APoly), n, k))
    # print(xzNoise(n, k, APoly, px, pz))
    # exit(0)

    # enumerator = np.tensordot(get_enum_tensor(code603, [3,0,1]) , get_enum_tensor(code603, [0,1]),axes = (2,0))
    # APoly = np.trace(enumerator, axis1=1, axis2=2)[0]
    # print(APoly)
    # print(simp_poly(APoly))
    # print("d", distance_from_poly(simp_poly(APoly),7,1))
    # print(xzNoise(7,1,APoly, px, pz))
    # APoly = Poly(simp_poly(APoly))

    exit(0)
    print(distance_from_poly(APoly, 7, 1))
