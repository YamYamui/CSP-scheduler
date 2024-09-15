from flask import Flask, request, jsonify
from generate import csp_solver 
from flask_cors import CORS
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set up CORS
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}}, supports_credentials=True)

@app.route('/api/solve', methods=['POST', 'OPTIONS'])
def solve():
    if request.method == 'OPTIONS':
        app.logger.info('OPTIONS request received')
        return '', 200

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
    app.run(debug=True, host='0.0.0.0')
