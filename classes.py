from itertools import combinations
from collections import deque, Counter
import calendar
import datetime
import csv


class Variable:
    def __init__(self, name, duty_type, duration, domain, constraints):
        self.name = name
        self.duty_type = duty_type
        self.duration = duration
        self.domain = domain
        self.constraints = constraints
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)

class CSPContext:
    def __init__(self, people, days, favour_consecutive, constraints, covers):
        self.variables = []
        self.days = days
        self.favour_consecutive = favour_consecutive
        self.people = people
        self.covers = covers

        # Initialize variables list with duties
        for day in range(1, days + 1):
            domain = list(combinations(people, 2))  
            day_constraints = [p for p, data in constraints.items() if day in data.get("cannot_work_on", [])]
            self.variables.append(Variable(name=f"{day}", duty_type="normal", duration=(day, day), domain=domain, constraints=day_constraints))

        # Initialize variables list with covers
        for cover in covers:
            domain = people
            cover_constraints = []
            for day in range(cover['start'], cover['end'] + 1):
                cover_constraints.extend([p for p, data in constraints.items() if day in data.get("cannot_work_on", [])])
            cover_constraints = list(set(cover_constraints))
            self.variables.append(Variable(name=cover['name'], duty_type="cover", duration=(cover['start'], cover['end']), domain=domain, constraints=cover_constraints))

class CSPSolver:
    def __init__(self, csp_context):
        self.csp_context = csp_context
    
    # Given the name of variable in assignment, return the actual variable object
    def get_variable(self, name):
        name = str(name)
        for v in self.csp_context.variables:
            if v.name == name:
                return v
        raise ValueError(f"No variable found with name: {name}")

    

    #  Enforcing arc-consistency across all the variables
    def ac3(self):
        queue = deque([(i, j) for i in self.csp_context.variables for j in self.csp_context.variables if i != j])
        while queue:
            (i, j) = queue.popleft()
            # with open("logs.txt", "a") as f:
            #     print(f"Processing arc ({i+1}, {j+1})", file = f)
            if self.revise(i, j):
                if not i.domain:
                    return False
                for k in self.csp_context.variables:
                    if k != i:
                        queue.append((k, i))
        return True

    # # Check if values of i are valid wrp to j
    # def revise(self, i, j):
    #     revised = False
    #     for x in self.csp_context.variables[i].domain[:]:
    #         if not any(self.is_consistent({j: y}, i + 1, x) for y in self.csp_context.variables[j].domain):
    #             self.csp_context.variables[i].domain.remove(x)
    #             revised = True
    #     return revised

    def revise(self, x, y):
        revised = False
        
        for x_value in x.domain[:]:  # Create a copy to iterate over
            # Check if there's a valid y_value for this x_value
            if not any(self.is_consistent({x.name: x_value, y.name: y_value}, y, y_value) 
                    for y_value in y.domain):
                        x.domain.remove(x_value)
                        revised = True
        
        return revised
    
    # Checking for constraints
    def is_consistent(self, assignment, variable, value):
        if variable.duty_type == "normal":
            day = variable.duration[0]

            # Check if assigned pair has cover on this day respectively
            for cover_variable_name, cover_person in assignment.items():
                cover_variable = self.get_variable(cover_variable_name)
                if cover_variable.duty_type == "cover":
                    if cover_variable.duration[0] <= day <= cover_variable.duration[1] and cover_person in value:
                        return False

            # Check for consecutive duties
            for person in value:
                # Check for three consecutive days
                if (str(day - 1) in assignment and person in assignment[str(day - 1)] and
                    str(day - 2) in assignment and person in assignment[str(day - 2)]):
                    return False
                if (str(day + 1) in assignment and person in assignment[str(day + 1)] and
                    str(day + 2) in assignment and person in assignment[str(day + 2)]):
                    return False
                # Check for d.x.d pattern
                if (str(day - 1) in assignment and person in assignment[str(day - 1)] and
                    str(day + 1) in assignment and person in assignment[str(day + 1)]):
                    return False
            
            # Check for covers the next day
            for cover_variable_name, cover_person in assignment.items():
                cover_variable = self.get_variable(cover_variable_name)
                if cover_variable.duty_type == "cover":
                    if cover_variable.duration[0] == day + 1  and cover_person in value:
                        return False   
            # Check block out dates
            if any(person in variable.constraints for person in value):
                return False

        elif variable.duty_type == "cover":

            # Check if assigned person has duty on this day
            for normal_variable_name in range(variable.duration[0], variable.duration[1] + 1):
                normal_variable = self.get_variable(normal_variable_name)
                if normal_variable.name in assignment and value in assignment[normal_variable.name]:
                        return False
            
            # Check if day before is buzy
            if variable.duration[0] - 1 in assignment and value in assignment[variable.duration[0] -1]:
                return False
        
            # Check block out dates
            if value in variable.constraints:
                return False

        return True

    def backtrack(self, assignment, duty_count, month, year):
        if len(assignment) == self.csp_context.days + len(self.csp_context.covers):
            return assignment

        # Choose variable with least values left in domain
        unassigned = [v for v in self.csp_context.variables if v.name not in assignment]
        variable = min(unassigned, key=lambda v: len(v.domain))

        # Sort to domain
        for value in self.order_domain_values(variable, duty_count, assignment):
            if self.is_consistent(assignment, variable, value):
                assignment[variable.name] = value
                is_weekend = datetime.date(year, month, variable.duration[0]).weekday() >= 5
                increment = 2 if is_weekend else 1

                # Point allocation
                if variable.duty_type == "normal":
                    duty_count[value[0]] += increment
                    duty_count[value[1]] += increment
                elif variable.duty_type == "cover":
                    cover_length = variable.duration[1] - variable.duration[0] + 1
                    duty_count[value] += cover_length

                result = self.backtrack(assignment, duty_count, month, year)

                # Assingments are filled, return to first function call
                if result:
                    return result
                
                # Backtrack
                assignment.pop(variable.name)
                duty_count[value[0]] -= increment
                duty_count[value[1]] -= increment

                if variable.duty_type == "normal":
                    duty_count[value[0]] -= increment
                    duty_count[value[1]] -= increment
                elif variable.duty_type == "cover":
                    cover_length = variable.duration[1] - variable.duration[0] + 1
                    duty_count[value] -= cover_length


        # None of the pairs are consistent, return None to backtrack and try another pair in the previous assignment
        return None

    def order_domain_values(self, var, duty_count, assignment):
        if var.duty_type == "normal":
            day = int(var.name)
            if self.csp_context.favour_consecutive == 1:
                return sorted(var.domain, key=lambda value: self.consecutive_duty_preference(day, value, assignment, duty_count))
            else:
                return sorted(var.domain, key=lambda value: sum(duty_count.get(p, 0) for p in value))
        elif var.duty_type == "cover":
            cover_length = var.duration[1] - var.duration[0] + 1
            return sorted(var.domain, key=lambda p: duty_count.get(p, 0) + cover_length)
    
    def consecutive_duty_preference(self, day, pair, assignment, duty_count):
        # Favor pairs that continue a sequence, but not more than 2 consecutive days
        consecutive_bonus = 0
        for person in pair:
            if str(day - 1) in assignment and person in assignment[str(day - 1)]:
                consecutive_bonus += 1  # Favor continuing a sequence
                if str(day - 2) in assignment and person in assignment[str(day - 2)]:
                    consecutive_bonus -= 1  # Penalize three consecutive days

            if str(day + 1) in assignment and person in assignment[str(day + 1)]:
                consecutive_bonus += 1  # Favor continuing a sequence
                if str(day + 2) in assignment and person in assignment[str(day + 2)]:
                    consecutive_bonus -= 1  # Penalize three consecutive days
            
            if str(day + 1) in assignment and str(day - 1) in assignment:
                consecutive_bonus -= 2


        # Balance between consecutive duty preference and current duty load
        balance_factor = sum(duty_count.get(p, 0) for p in pair)

        # The lower the score, the better the pair fits the preference
        return - consecutive_bonus + balance_factor

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
    
    def nice_print(self, assignment, people, month, days, year): 
        # Formating header rows
        start_day = calendar.monthrange(year, month)[0]
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_row = [days_of_week[(start_day + i) % 7] for i in range(days)]
        date_row = [(i + 1) for i in range(days)]
        header_days = ["Days"] + day_row
        header_dates = ["Dates"] + [f"{day:02d}." for day in date_row]
        cover_list = []

        for variable in self.csp_context.variables:
            if variable.duty_type == "cover":
                cover_list.append(variable)

        # Duty Roster
        duty_roster = [[None for i in range(days)] for j in range(len(people))]
        
        for j in range(days):
            for i in range(len(people)):
                if i == people.index(assignment[str(j + 1)][0]):
                    duty_roster[i][j] = "P1"
                if i == people.index(assignment[str(j + 1)][1]):
                    duty_roster[i][j] = "P2"
                for cover in cover_list:
                    if cover.duration[0] <= j + 1 <= cover.duration[1]:
                        if i == people.index(assignment[cover.name]):
                            duty_roster[i][j] = cover.name

        
        # Output to CSV file
        with open('output.csv', 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(header_days)
            writer.writerow(header_dates)
            for i, row in enumerate(duty_roster):
                row_str = [f"{people[i]} "] + [str(cell) if cell is not None else "  " for cell in row]
                writer.writerow(row_str)

    