#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________

#
# Robust Knapsack Problem
#

from pyomo.environ import ConcreteModel, Set, Binary, Var, Constraint
from pyomo.environ import Objective, maximize, ConstraintList, SolverFactory
from romodel import UncSet, UncParam
from romodel.uncset import EllipsoidalSet, PolyhedralSet
import itertools
import numpy as np


def Knapsack():
    tools = ['hammer', 'wrench', 'screwdriver', 'towel']
    v = {'hammer': 8, 'wrench': 3, 'screwdriver': 6, 'towel': 11}
    w = {'hammer': 5, 'wrench': 7, 'screwdriver': 4, 'towel': 3}

    limit = 14

    M = ConcreteModel()

    M.ITEMS = Set(initialize=v.keys())
    M.x = Var(M.ITEMS, within=Binary)

    # Define Uncertainty set & uncertain parameters
    mu = [w[t] for t in tools]
    A = [[0.1, 0.01, 0.0, 0.0],
         [0.01, 0.1, 0.0, 0.0],
         [0.0, 0.0, 0.1, 0.0],
         [0.0, 0.0, 0.0, 0.1]]
    Sig = np.linalg.inv(A).tolist()
    perm = itertools.product([1, -1], repeat=len(tools))
    P = [i for i in perm]
    rhs = [sum(p[i]*w[t] for i, t in enumerate(tools)) + 5.5 for p in P]

    M.E = UncSet()
    M.w = UncParam(M.ITEMS, uncset=M.E, nominal=w)
    w = M.w

    # Ellipsoidal set
    # direct
    lhs = 0
    for i, ti in enumerate(tools):
        for j, tj in enumerate(tools):
            lhs += (w[ti] - mu[i])*A[i][j]*(w[tj] - mu[j])
    M.E.cons = Constraint(expr=lhs <= 1)
    # library
    # An ellipsoidal constraint has the form (w - mu)^T Sig^-1 (w - mu)
    # EllipsoidalSet takes mu and Sig as arguments (inverse of A above)
    M.Elib = EllipsoidalSet(mu, Sig)

    # Polyhedral set
    # direct
    M.P = UncSet()
    M.P.cons = ConstraintList()
    for i, p in enumerate(P):
        M.P.cons.add(sum(M.w[t]*p[i] for i, t in enumerate(tools)) <= rhs[i])
    # library
    M.Plib = PolyhedralSet(P, rhs)

    M.value = Objective(expr=sum(v[i]*M.x[i] for i in M.ITEMS), sense=maximize)
    M.weight = Constraint(expr=sum(w[i]*M.x[i] for i in M.ITEMS) <= limit)

    return M


if __name__ == '__main__':
    m = Knapsack()
    solver = SolverFactory('romodel.cuts')
    solver.solve(m)
