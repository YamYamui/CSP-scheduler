from itertools import combinations
from collections import deque, Counter

class Variable:
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain
        self.constraints = []
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)
    
    def is_consistent(self, pair, assignment):
        # Implement constraint checking logic
        for person in pair:
            consecutive_count = 0
            for d in range(len(assignment), len(assignment) - 2, -1):
                if d in assignment and person in assignment[d]:
                    consecutive_count += 1
                else:
                    break
            if consecutive_count >= 2:
                return False
        return True

class CSPContext:
    def __init__(self, people, days):
        self.variables = {}
        self.constraints = []
        self.domains = {i: list(combinations(people, 2)) for i in range(1, days + 1)}
        self.days = days
    
    def add_variable(self, name, domain):
        self.variables[name] = Variable(name, domain)
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)
    
    def get_variable(self, name):
        return self.variables.get(name)
    
    def is_consistent(self, assignment):
        for var in self.variables.values():
            if not var.is_consistent(assignment.get(var.name, ()), assignment):
                return False
        return True

class CSPSolver:
    def __init__(self, csp_context):
        self.csp_context = csp_context
    
    def ac3(self):
        queue = deque([(i, j) for i in range(1, self.csp_context.days + 1) for j in range(1, self.csp_context.days + 1) if i != j])
        while queue:
            (i, j) = queue.popleft()
            if self.revise(i, j):
                if not self.csp_context.domains[i]:
                    return False
                for k in range(1, self.csp_context.days + 1):
                    if k != i:
                        queue.append((k, i))
        return True

    def revise(self, i, j):
        revised = False
        for x in self.csp_context.domains[i][:]:
            if not any(self.is_consistent({j: y}, i, x) for y in self.csp_context.domains[j]):
                self.csp_context.domains[i].remove(x)
                revised = True
        return revised

    def is_consistent(self, assignment, day, pair):
        for person in pair:
            consecutive_count = 0
            for d in range(day-1, day-3, -1):
                if d in assignment and person in assignment[d]:
                    consecutive_count += 1
                else:
                    break
            if consecutive_count >= 2:
                return False
        return True

    def backtrack(self, assignment, duty_count):
        if len(assignment) == self.csp_context.days:
            return assignment

        # Find the next day to assign
        day = min(d for d in range(1, self.csp_context.days + 1) if d not in assignment)

        # Sort pairs based on the total number of duties assigned so far
        sorted_pairs = sorted(self.csp_context.domains[day], key=lambda pair: duty_count[pair[0]] + duty_count[pair[1]])

        for pair in sorted_pairs:
            if self.is_consistent(assignment, day, pair):
                assignment[day] = pair
                duty_count[pair[0]] += 1
                duty_count[pair[1]] += 1
                result = self.backtrack(assignment, duty_count)
                if result:
                    return result
                # Backtrack
                assignment.pop(day)
                duty_count[pair[0]] -= 1
                duty_count[pair[1]] -= 1
        return None

