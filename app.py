from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

# Simulation Classes
class Person:
    def __init__(self, ID, num_of_floors):
        self.ID = ID
        self.cur_floor = random.randint(1, num_of_floors)
        self.dst_floor = random.randint(1, num_of_floors)
        while self.dst_floor == self.cur_floor:
            self.dst_floor = random.randint(1, num_of_floors)
        self.in_elevator = False
        self.finished = False

class Elevator:
    def __init__(self, num_of_floors):
        self.cur_floor = 1
        self.direction = 1
        self.people = []  # People inside the elevator
        self.requests = set()
        self.num_of_floors = num_of_floors
        self.pause_counter = 0  # Pause counter for frame-based boarding/alighting
        self.pause_action = None  # Track action: "boarding" or "alighting"
        self.target_person = None  # Track person being processed

    def update_requests(self, people_list):
        self.requests.clear()
        for p in people_list:
            if not p.finished:
                if not p.in_elevator:
                    self.requests.add(p.cur_floor)
                else:
                    self.requests.add(p.dst_floor)

    def process_people(self, people_list):
        # If in pause mode, allow only one person to board/alight in this frame
        if self.pause_counter > 0:
            self.pause_counter -= 1
            return True  # Stay on the same floor

        # Handle people exiting
        for p in self.people[:]:
            if p.dst_floor == self.cur_floor:
                p.finished = True
                p.in_elevator = False
                self.people.remove(p)
                self.pause_counter = 1  # Pause for one frame
                self.pause_action = "alighting"
                self.target_person = p
                return True

        # Handle people entering (one by one)
        for p in people_list:
            if p.cur_floor == self.cur_floor and not p.finished and not p.in_elevator and len(self.people) < 5:
                p.in_elevator = True
                self.people.append(p)
                self.pause_counter = 1  # Pause for one frame
                self.pause_action = "boarding"
                self.target_person = p
                return True

        # Reset action tracking
        self.pause_action = None
        self.target_person = None
        return False  # No people to process

    def move(self):
        if self.pause_counter > 0:  # Stay on the floor if pausing
            return True
        if not self.requests:
            return False  # Stop if no requests remain
        if self.direction == 1 and self.cur_floor == self.num_of_floors:
            self.direction = -1
        elif self.direction == -1 and self.cur_floor == 1:
            self.direction = 1
        self.cur_floor += self.direction
        return True

# Initialize Variables
NUM_OF_FLOORS = 10
people = []
elevator = Elevator(NUM_OF_FLOORS)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/init", methods=["POST"])
def initialize():
    global people, elevator
    num_of_people = int(request.form.get("num_people", 5))
    if num_of_people > 5:  # Limit check
        return jsonify({"error": "Maximum number of people is 5."}), 400
    if num_of_people < 1:  # Limit check
        return jsonify({"error": "Minimum number of people is 1."}), 400
    people = [Person(i+1, NUM_OF_FLOORS) for i in range(num_of_people)]
    elevator = Elevator(NUM_OF_FLOORS)
    return jsonify({"status": "Simulation initialized", "num_people": num_of_people})

@app.route("/update", methods=["GET"])
def update():
    global elevator
    # Update elevator requests
    elevator.update_requests(people)

    # Process one person per frame (board or alight)
    processing_done = elevator.process_people(people)

    # If no people are being processed, allow the elevator to move
    if not processing_done:
        elevator_moved = elevator.move()
    else:
        elevator_moved = True

    # Generate text-based graphic
    building_representation = generate_building_text()

    # Return updated state
    return jsonify({
        "building_text": building_representation,
        "simulation_complete": not elevator_moved
    })

def generate_building_text():
    building = []
    for floor in range(NUM_OF_FLOORS, 0, -1):
        left_people = " ".join([f"P{p.ID}" for p in people if p.cur_floor == floor and not p.finished and not p.in_elevator])
        right_people = " ".join([f"P{p.ID}" for p in people if p.finished and p.dst_floor == floor])

        # Show elevator ONLY on its current floor
        if elevator.cur_floor == floor:
            elevator_content = " ".join([f"P{p.ID}" for p in elevator.people]) or "  "
            elevator_display = f"| [{elevator_content:^17}] |"
        else:
            elevator_display = "|                     |"

        # Add floor representation
        floor_line = f"{left_people:<26}{elevator_display}{right_people:>26}"
        building.append(floor_line)
        building.append("-" * 75)  # Add floor separator

    return "\n".join(building)

if __name__ == "__main__":
    app.run(debug=True)
