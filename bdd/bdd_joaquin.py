from pysat.formula import CNF
from pysat.solvers import Glucose4

# Define the UVL model
uvl_model = {
    'A': {'a1', 'a2'},
    'B': {'b1', 'b2', 'b3'},
    'C': {'c1', 'c2'}
}
constraints = [
    ('A', 'a1', [('B', 'b1'), ('B', 'b2')]),
    ('A', 'a2', [('B', 'b2'), ('B', 'b3')]),
    ('B', 'b1', [('C', 'c1')]),
    ('B', 'b3', [('C', 'c2')])
]

# Create a CNF formula from the UVL model
cnf = CNF()
variable_map = {}
next_variable_id = 1

for feature, values in uvl_model.items():
    for value in values:
        variable = f'{feature}_{value}'
        variable_map[variable] = next_variable_id
        next_variable_id += 1
        cnf.append([variable_map[variable]])

for feature, value, implies in constraints:
    variable = f'{feature}_{value}'
    clause = [-variable_map[variable]]
    for feature2, value2 in implies:
        variable2 = f'{feature2}_{value2}'
        clause.append(variable_map[variable2])
    cnf.append(clause)

# Apply the Tseitin transformation to the CNF formula
cnf_tseitin = cnf.tseitin()

# Solve the SAT problem using a SAT solver (e.g. Glucose4)
solver = Glucose4()
solution = solver.solve(cnf_tseitin)

if solution:
    # Extract the variable assignments from the solver
    assignments = [None] * (len(variable_map) + 1)
    for variable, value in solver.get_model():
        if variable > 0:
            assignments[variable] = 1 if value else 0
        else:
            assignments[-variable] = 0 if value else 1
    # Print the variable assignments
    for variable, variable_id in variable_map.items():
        value = 'True' if assignments[variable_id] else 'False'
        print(f'{variable}: {value}')
else:
    print('UNSAT')
