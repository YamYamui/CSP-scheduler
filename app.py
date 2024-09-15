from flask import Flask, request, jsonify
from generate import csp_solver 

app = Flask(__name__)

# API endpoint to solve CSP
@app.route('/api/solve', methods=['POST'])
def solve():
    try:
        # Get the JSON input from the POST request
        json_data = request.get_json()

        # Call the CSP solver with the input data (a dictionary)
        result = csp_solver(json_data)

        # Return the result as a JSON response
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
if __name__ == '__main__':
    app.run()
