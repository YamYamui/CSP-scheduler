import sys
import calendar

def main():

    if len(sys.argv) not in [3]:
        sys.exit("Usage: python generate.py month pax")

    # Get info of month and pax 
    month = calendar.monthcalendar(2024,int(sys.argv[1]))
    pax = sys.argv[2]

    # Generate schedule
    schedule = Schedule(structure, words)
    creator = Schedule_Creator(schedule)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)

if __name__ == "__main__":
    main()