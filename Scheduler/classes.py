from itertools import combinations
from collections import deque, Counter
import calendar
import datetime

class Variable:
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain
        self.constraints = []
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)

class CSPContext:
    def __init__(self, people, days, favour_consecutive, constraints):
        self.variables = []
        self.days = days
        self.favour_consecutive = favour_consecutive
    
        # Initialize a list of variables
        for day in range(1, days + 1):
            domain = list(combinations(people, 2))  
            self.variables.append(Variable(day, domain))

        # Update Constraints in variables
        if constraints:
            for personnel in constraints:
                if constraints[personnel]["cannot_work_on"]:
                    for dates in constraints[personnel]["cannot_work_on"]:
                        self.variables[dates - 1].constraints.append(personnel)


class CSPSolver:
    def __init__(self, csp_context):
        self.csp_context = csp_context
    
    #  Enforcing arc-consistency across all the variables
    def ac3(self):
        queue = deque([(i, j) for i in range(len(self.csp_context.variables)) for j in range(len(self.csp_context.variables)) if i != j])
        while queue:
            (i, j) = queue.popleft()
            if self.revise(i, j):
                if not self.csp_context.variables[i].domain:
                    return False
                for k in range(self.csp_context.days):
                    if k != i:
                        queue.append((k, i))
        return True

    # Check if values of i are valid wrp to j
    def revise(self, i, j):
        revised = False
        for x in self.csp_context.variables[i].domain[:]:
            if not any(self.is_consistent({j: y}, i, x) for y in self.csp_context.variables[j].domain):
                self.csp_context.variables[i].domain.remove(x)
                revised = True
        return revised

    # Checking for constraints
    def is_consistent(self, assignment, day, pair):
        # Check for consecutive duties
        for person in pair:
            consecutive_count = 0
            for d in range(day-1, day-3, -1):
                if d in assignment and person in assignment[d]:
                    consecutive_count += 1
                else:
                    break
            if consecutive_count >= 2:
                return False
    
        # Check for block out dates
        for person in pair:
            if person in self.csp_context.variables[day - 1].constraints:
                return False
        
        return True

    def backtrack(self, assignment, duty_count, month):
        if len(assignment) == self.csp_context.days:
            return assignment

        # Apply the Minimum Remaining Values (MRV) heuristic
        # Actual day
        day = min(
            (d for d in range(len(self.csp_context.variables)) if d + 1 not in assignment),
            key=lambda d: len(self.csp_context.variables[d].domain)
        ) + 1

        if self.csp_context.favour_consecutive == 0:
            # Sort pairs based on the Least Constraining Value (LCV) heuristic
            sorted_pairs = sorted(
                self.csp_context.variables[day - 1].domain,
                key=lambda pair: self.lcv_heuristic(day, pair, duty_count)
            )
        elif self.csp_context.favour_consecutive == 1:
            # Sort pairs based on preference for consecutive duties
            sorted_pairs = sorted(
                self.csp_context.variables[day - 1].domain,
                key=lambda pair: self.consecutive_duty_preference(day, pair, assignment, duty_count)
            )

        for pair in sorted_pairs:
            if self.is_consistent(assignment, day, pair):
                assignment[day] = pair
                if datetime.date(2024, month , day).weekday() >= 5:
                    duty_count[pair[0]] += 2
                    duty_count[pair[1]] += 2
                else:
                    duty_count[pair[0]] += 1
                    duty_count[pair[1]] += 1
                result = self.backtrack(assignment, duty_count, month)
                if result:
                    return result
                # Backtrack
                assignment.pop(day)
                if datetime.date(2022, month , day).weekday() >= 5:
                    duty_count[pair[0]] -= 2
                    duty_count[pair[1]] -= 2
                else:
                    duty_count[pair[0]] -= 1
                    duty_count[pair[1]] -= 1
        return None

    def lcv_heuristic(self, day, pair, duty_count):
        # Least Constraining Value (LCV) heuristic combined with duty day balancing
        reduced_options = 0

        # Evaluate the impact of choosing `pair` on future days
        for future_day in range(day, self.csp_context.days):
            future_variable = self.csp_context.variables[future_day]
            valid_pairs_count = 0

            for future_pair in future_variable.domain:
                # Check if the future pair is valid if `pair` is chosen for `day`
                if self.is_consistent({day: pair},day, future_pair):
                    valid_pairs_count += 1

            # Increment reduced_options based on the count of valid future pairs
            reduced_options += len(future_variable.domain) - valid_pairs_count

        # Combine LCV heuristic with a duty balancing component
        balance_factor = duty_count[pair[0]] + duty_count[pair[1]]

        # The LCV heuristic favors pairs that leave more options open for future days
        return reduced_options + balance_factor

    
    def consecutive_duty_preference(self, day, pair, assignment, duty_count):
        # Favor pairs that continue a sequence, but not more than 2 consecutive days
        consecutive_bonus = 0
        for i, person in enumerate(pair):
            if day > 1:
                if day - 1 in assignment and person in assignment[day - 1]:
                    consecutive_bonus += 1  # Favor continuing a sequence

        # Balance between consecutive duty preference and current duty load
        balance_factor = duty_count[pair[0]] + duty_count[pair[1]]

        # The lower the score, the better the pair fits the preference
        return (2 - consecutive_bonus) * 1000 + balance_factor

    def nice_print(self, assignment, people, month, days): 
        start_day = calendar.monthrange(2024, month)[0]

        duty_roster = [["|  " for i in range(len(assignment))] for j in range(len(people))]
        
        for j in range(len(assignment)):
            for i in range(len(people)):
                if i == people.index(assignment[j + 1][0]):
                    duty_roster[i][j] = "|P1"
                if i == people.index(assignment[j + 1][1]):
                    duty_roster[i][j] = "|P2"

        # Days of the week and dates
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_row = [days_of_week[(start_day + i) % 7] for i in range(days)]
        date_row = [(i + 1) for i in range(days)]
        
        # Create the header with days and dates with dots
        header_days = "  ".join(day_row)
        header_dates = "  ".join(f"{day:02d}." for day in date_row)
        
        # Define row and column separators
        row_separator = "+" + "----+" * (days + 1)  # Extra column for baker names
        header_separator = "+" + "----+" * (days + 1)  # Extra column for baker names
        
        # Print header
        print(row_separator)
        print("| Bak" + "  " + header_days + "|")
        print(header_separator)
        print("|  " + "    " + header_dates + "|")
        print(row_separator)
        
        # Print duty roster
        for i, row in enumerate(duty_roster):
            row_str = f"{people[i]} " + "  ".join(str(cell) if cell is not None else "  " for cell in row)
            print("| " + row_str + "  |")
            print(row_separator)
