from abc import ABCMeta, abstractmethod
import sys
from gurobipy import *
import igraph as ig

from .separation import *

class KPPBase(metaclass=ABCMeta):
  def __init__(self, G, k, verbosity=1):
    self.G=G
    self.model=Model()
    self.model.modelSense=GRB.MINIMIZE
    self.k = k
    self.y={}
    self.model.setParam("OutputFlag", 0)
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      self.y[u,v] = self.model.addVar(obj=1.0,ub=1.0)
    self.x={}
    self.z={}
    self.constraints=[]
    self.sep_algs=[]
    self.out = sys.stdout
    self.verbosity=verbosity

  def get_solution(self):
    return Solution(self.model.getAttr('x', self.x), 
                    self.model.getAttr('x', self.y),
                    self.model.getAttr('x', self.z))

  def cut(self):
    if self.x:
      raise RuntimeError('Cutting plan algorithm can only be used before node variables have been added')

    if self.verbosity > 0:
      print('Running cutting plane algorithms', file=self.out)

    it_count=0
    total_added=0
    while True:
      it_count+=1
      self.model.optimize()
      if self.verbosity > 1:
        print('\n', 10*'-', 'Iteration ', it_count,
              10*'-', file=self.out)
        print(" Objective value: ", self.model.objVal, file=self.out)
      new_constraints=[]
      sol = self.get_solution()
      for sep_alg in self.sep_algs:
        constr_list=sep_alg.find_violated_constraints(sol, self.verbosity-1)
        new_constraints.extend(constr_list)
        
      total_added+=len(new_constraints)
      for constr in new_constraints:
        self.add_constraint(constr)
      if not new_constraints:
        if self.verbosity > 1:
          print(' Found no constraints to add; exiting cutting plane loop', file=self.out)
        if self.verbosity > 0:
          print(' Added a total of', total_added, 'constraints', file=self.out)
          print(' Lower bound: ', self.model.objVal)
        break

    return total_added

  def remove_redundant_constraints(self, hard=False, allowed_slack=1e-3):
    slack, dual = 0, 0
    to_remove=[]

    for constr in self.constraints:
      if abs(constr.Slack) > allowed_slack:
        to_remove.append(constr)
        slack+=1
      elif hard and constr.Pi==0.0:
        to_remove.append(constr)
        dual+=1
          
    for constr in to_remove:
      self.model.remove(constr)
      self.constraints.remove(constr)
    
    if self.verbosity > 0:
      print(" Removed", slack, "constraints with slack greater than", allowed_slack, file=self.out)
      print(" Removed", dual, "constraints with zero dual variable", file=self.out)
      print("", len(self.constraints), "constraints remaining", file=self.out)

    self.model.update()
    return slack+dual

  def add_separator(self, sep_alg):
    self.sep_algs.append(sep_alg)

  def add_constraint(self, constraint):
    expr=LinExpr()
    for e,coef in constraint.x_coefs.items():
      expr.addTerms(coef, self.x[e])
    for e,coef in constraint.y_coefs.items():
      expr.addTerms(coef, self.y[e])
    for e,coef in constraint.z_coefs.items():
      expr.addTerms(coef, self.z[e])
    if constraint.op=='<':
      cons=self.model.addConstr(expr<=constraint.rhs)
    elif constraint.op=='>':
      cons=self.model.addConstr(expr>=constraint.rhs)
    elif constraint.op=='==':
      cons=self.model.addConstr(expr==constraint.rhs)
    self.constraints.append(cons)

  def solve(self):
    n = self.G.vcount()
    if not self.x: self.add_node_variables()
    if self.verbosity > 0:
      print("Running branch-and-bound", file=self.out)
    self.model.optimize()
    if self.verbosity > 0:
      print(" Optimal objective value: ", self.model.objVal, file=self.out)

  @abstractmethod
  def add_node_variables(self):
    pass

  @abstractmethod
  def print_solution(self):
    pass

class KPP(KPPBase):
  def __init__(self, G, k, verbosity=1):
    KPPBase.__init__(self, G, k, verbosity)

  def add_node_variables(self):
    n=self.G.vcount()
    for i in range(n):
      for j in range(self.k):
        self.x[i,j] = self.model.addVar(vtype=GRB.BINARY)
        
    self.model.update()
      
    for i in range(n):
      total_assign = LinExpr()
      for j in range(self.k):
        total_assign.addTerms(1.0, self.x[i,j])
      self.model.addConstr(total_assign == 1.0)

    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      for i in range(self.k):
        self.model.addConstr(self.y[u,v] >= self.x[u,i] + self.x[v,i] - 1.0)
        self.model.addConstr(self.x[u,i] >= self.x[v,i] + self.y[u,v] - 1.0)
        self.model.addConstr(self.x[v,i] >= self.x[u,i] + self.y[u,v] - 1.0)
    self.model.update()

  def break_symmetry(self):
    if self.verbosity > 0:
      print("Adding symmetry breaking constraints")
    if not self.x: self.add_node_variables()
    for i in range(self.k-1):
      sym = LinExpr()
      for j in range(i+1):
        sym.addTerms(1.0, self.x[i,j])
    self.model.addConstr(sym == 1)
    self.model.update()

  def print_solution(self):
    sol = self.get_solution()
    x, y = sol.x, sol.y
    clusters = []
    for i in range(k):
      cluster = []
      for j in range(n):
        if abs(x[j,i] - 1.0) < 1e-4:
          cluster.append(j)
      clusters.append(cluster)
    for i in range(k):
      print("Colour", i,": ", clusters[i], file=self.out)

    print("Clashes: ", file=self.out)
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if abs(y[u,v] - 1.0) < 1e-4:
        print((u,v), end=', ', file=self.out)
    print('\n', file=self.out)

class KPPExtension(KPPBase):
  def __init__(self, G, k, verbosity=1):
    KPPBase.__init__(self, G, k, verbosity)
    
  def add_z_variables(self):
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      self.z[u,v] = self.model.addVar(obj=1.0, ub=1.0)

  def add_node_variables(self):
    if not self.z: self.add_z_variables()
    n=self.G.vcount()
    for i in range(n):
      for j in range(2*self.k):
        self.x[i,j] = self.model.addVar(vtype=GRB.BINARY)
        
    self.model.update()

    for i in range(n):
      total_assign = LinExpr()
      for j in range(2*self.k):
        total_assign.addTerms(1.0, self.x[i,j])
      self.model.addConstr(total_assign == 1.0)

    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      for c in range(self.k):
        self.model.addConstr(self.y[u,v] >= self.x[u,c] + self.x[u,c+self.k] + self.x[v,c] + self.x[v,c+self.k] - 1.0)

    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      for c in range(2*self.k):
        self.model.addConstr(self.z[u,v] >= self.x[u,c] + self.x[v,c] - 1.0)
        self.model.addConstr(self.x[u,c] >= self.x[v,c] + self.z[u,v] - 1.0)
        self.model.addConstr(self.x[v,c] >= self.x[u,c] + self.z[u,v] - 1.0)

  def break_symmetry(self):
    if not self.G.vcount() > 2*self.k:
      if self.verbosity > 0:
        print('Too few nodes to add symmetry breaking constraints')
    else:
      if self.verbosity > 0:
        print("Adding symmetry breaking constraints")
      if not self.x: self.add_node_variables()
      for i in range(self.k):
        expr = LinExpr()
        for c in range(i+1): 
          expr.addTerms(1.0, self.x[i,c])
        for c in range(self.k,self.k+i): 
          expr.addTerms(1.0, self.x[i,c])

    # self.model.addConstr(self.x[0,0] == 1.0)
    # self.model.addConstr(self.x[1,0] + self.x[1,1] + self.x[1,3] == 1.0)
    # #self.model.addConstr(self.x[2,0] + self.x[2,1] + self.x[2,2] + self.x[2,3] + self.x[2,4] == 1.0)    
    # self.model.addConstr(self.x[2,5]==0.0)
    # self.model.update()

  def print_solution(self):
    sol = self.get_solution()
    x, y, z = sol.x, sol.y, sol.z
    clusters = []
    n = self.G.vcount()
    if x:
      for c in range(2*self.k):
        cluster = []
        for j in range(n):
          if abs(x[j,c] - 1.0) < 1e-4:
            cluster.append(j)
        clusters.append(cluster)
      for i in range(2*self.k):
        print("Colour", i,": ", clusters[i], file=self.out)

    print("3-Clashes: ")
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if abs(y[u,v] - 1.0) < 1e-4:
        print((u,v), end=', ', file=self.out)
    print('\n', file=self.out)

    print("6-Clashes: ")
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if abs(z[u,v] - 1.0) < 1e-4:
        print((u,v), end=', ', file=self.out)
    print('\n', file=self.out)
