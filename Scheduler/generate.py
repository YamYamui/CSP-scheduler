from classes import *
import calendar
import sys

def nice_print(assignment, people, month): 
    num_days = calendar.monthrange(2024, month)[1]
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
    day_row = [days_of_week[(start_day + i) % 7] for i in range(num_days)]
    date_row = [(i + 1) for i in range(num_days)]
    
    # Create the header with days and dates with dots
    header_days = "  ".join(day_row)
    header_dates = "  ".join(f"{day:02d}." for day in date_row)
    
    # Define row and column separators
    row_separator = "+" + "----+" * (num_days + 1)  # Extra column for baker names
    header_separator = "+" + "----+" * (num_days + 1)  # Extra column for baker names
    
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

def main():

    if len(sys.argv) not in [3]:
        sys.exit("Usage: python generate.py month pax")

    # Get info of month and pax 
    month = int(sys.argv[1])
    pax = int(sys.argv[2])
    days = calendar.monthrange(2024, month)[1]

    people = [f"P{i}" for i in range(1, pax + 1)]

    # Initialize CSP context
    csp_context = CSPContext(people, days)

    # Define and add constraints here if needed

    # Initialize solver
    solver = CSPSolver(csp_context)

    # Running AC-3 preprocessing
    if not solver.ac3():
        assignment = None
    else:
        # Initialize duty count
        duty_count = Counter()
        
        # Running backtracking with balancing to find a solution
        assignment = solver.backtrack({}, duty_count)

    # Collating duty days for each individual
    if assignment:
        duty_count = Counter(person for pair in assignment.values() for person in pair)
        for day, pair in sorted(assignment.items()):
            print(f"Day {day}: {pair}")
        print("\nDuty Count:")
        for person, count in sorted(duty_count.items()):
            print(f"{person}: {count} days")
        nice_print(assignment, people, month)
    else:
        print("No solution found")

if __name__ == "__main__":
    main()