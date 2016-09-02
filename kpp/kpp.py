import sys
from gurobipy import *
import igraph as ig

from .separation import *

class KPP:
  def __init__(self, G, k):
    self.G=G
    self.k=k
    self.model=Model()
    self.model.modelSense=GRB.MINIMIZE
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

  def get_y_values(self):
    return self.model.getAttr('x', self.y)
    
  def add_separator(self, sep_alg):
    self.sep_algs.append(sep_alg)

  def add_constraint(self, constraint):
    expr=LinExpr()
    for e,coef in constraint.y_coefs.items():
      expr.addTerms(coef, self.y[e])
    # for e,coef, in constraint.z_coefs:
    #   expr.addTerms(coef, self.z[e])
    if constraint.op=='<':
      cons=self.model.addConstr(expr<=constraint.rhs)
    elif constraint.op=='>':
      cons=self.model.addConstr(expr>=constraint.rhs)
    elif constraint.op=='==':
      cons=self.model.addConstr(expr==constraint.rhs)
    self.constraints.append(cons)

  def discretize(self):
    for var in self.y.values(): var.vtype='B'
    for var in self.z.values(): var.vtype='B'
    self.model.update()

  def cut(self):
    if self.x:
      raise RuntimeError('Cutting plan algorithm can only be used before node variables have been added')

    print(50*'-', file=self.out)
    print('Running cutting plane algorithms', file=self.out)
    print(50*'-', file=self.out)

    it_count=0
    total_added=0
    while True:
      it_count+=1
      print('\n', 10*'-', 'Iteration ', it_count,
            10*'-', file=self.out)
      self.model.optimize()
      print(" Objective value: ", self.model.objVal, file=self.out)
      new_constraints=[]
      y = self.get_y_values()
      #print(y)
#      z = self.get_z_values()
      for sep_alg in self.sep_algs:
        constr_list=sep_alg.find_violated_constraints(y)
        new_constraints.extend(constr_list)
        
      total_added+=len(new_constraints)
      for constr in new_constraints:
        self.add_constraint(constr)
      if not new_constraints:
        print(' Found no constraints to add; exiting cutting plane loop', file=self.out)
        print(' Added a total of', total_added, 'constraints', file=self.out)
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
        
    print("Removed", slack, "constraints with slack greater than", allowed_slack, file=self.out)
    print("Removed", dual, "constraints with zero dual variable", file=self.out)
    print(len(self.constraints), "constraints remaining", file=self.out)

    self.model.update()
    return slack+dual

  def add_node_variables(self):
    for i in range(self.G.vcount()):
      for j in range(self.k):
        self.x[i,j] = self.model.addVar(vtype=GRB.BINARY)
        
    self.model.update()
      
    for i in range(self.G.vcount()):
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

  def solve(self):
    n = self.G.vcount()
    print("Solving k-partition problem", file=self.out)
    self.discretize()
    if not self.x: self.add_node_variables()
    
    self.model.optimize()
    print("Optimal objective value: ", self.model.objVal, file=self.out)
    x = self.model.getAttr('x', self.x)
    y = self.get_y_values()
    clusters = []
    for i in range(k):
      cluster = []
      for j in range(n):
        if abs(x[j,i] - 1.0) < 1e-4:
          cluster.append(j)
      clusters.append(cluster)
    for i in range(k):
      print("Colour", i,": ", clusters[i], file=self.out)

    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if abs(y[u,v] - 1.0) < 1e-4:
        print((u,v), end=', ', file=self.out)
    print('\n', file=self.out)

if __name__=='__main__':
  n, R = 30, 0.25
  G = ig.Graph.GRG(n, R)
  print(G)
  print(G.maximal_cliques())
  k = 3

  kpp = KPP(G, k)

  sep_alg_1 = CliqueSeparator(G.maximal_cliques(), k+1, k)
  sep_alg_2 = CliqueSeparator(G.maximal_cliques(), k+2, k)
  kpp.add_separator(sep_alg_1)
  kpp.add_separator(sep_alg_2)
  kpp.cut()
  kpp.remove_redundant_constraints(True)
  kpp.solve()
