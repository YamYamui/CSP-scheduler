from classes import *
import calendar
import sys
import json

def main():

    if len(sys.argv) != 2:
        sys.exit("Usage: python generate.py config.json")

    # Load the JSON configuration file
    config_file = sys.argv[1]
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        sys.exit(f"Error: The file {config_file} was not found.")
    except json.JSONDecodeError:
        sys.exit(f"Error: Failed to decode JSON from the file {config_file}.")
    
    # Get info from json file
    month = config.get("month")
    pax = config.get("pax")
    favor_consecutive = config.get("favor_consecutive")
    constraints = config.get("constraints", {})

    # Essential info
    if not all([month, pax]):
        sys.exit("Error: Missing parameters in JSON file.")

    # Derived info
    days = calendar.monthrange(2024, month)[1]
    people = [f"M{i}" for i in range(1, pax + 1)]

    # Initialize CSP context
    csp_context = CSPContext(people, days, favor_consecutive, constraints)

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
        assignment = solver.backtrack({}, duty_count, month)

    # Collating duty days for each individual
    if assignment:
        # duty_count = Counter(person for pair in assignment.values() for person in pair)
        # for day, pair in sorted(assignment.items()):
        #     print(f"Day {day}: {pair}")
        print("\nDuty Points:")
        for person, count in sorted(duty_count.items()):
            print(f"{person}: {count} Points")
        solver.nice_print(assignment, people, month, days)
    else:
        print("No solution found")

if __name__ == "__main__":
    main()