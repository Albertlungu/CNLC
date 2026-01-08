"""
./backend/api/server.py

Entry point for web API. The main file that ties everything together.
"""

import sys
import os
from typing import Union, Tuple, Any, Literal

from flask import Flask, Response, jsonify, request, make_response
from flask_cors import CORS

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import backend.core.business_manager as bm
import backend.storage.json_handler as jh

app = Flask(__name__) # Creating the flask application

CORS(app, origins="*") # Allow all origins to interact with webpage

app.config['JSON_SORT_KEYS'] = False # Preserves original JSON mappings
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# ================== Error handling ================

@app.errorhandler(404)
def not_found(error):
    """
    Handling 404 errors with a JSON response
    """
    return jsonify({"error": "Resource not found."}), 404

@app.errorhandler(400)
def bad_request(error):
    """
    Handle 400 errors with a JSON response (Pydantic validation)
    """
    return jsonify({"error": "Invalid request."}), 400

@app.errorhandler(500)
def server_error(error):
    """
    Handle 500 errors with a JSON response (internal server error)
    """
    return jsonify({"error": "Internal server error."}), 500


# ======================= Health check ======================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check to ensure that server is running
    """
    return jsonify({"status": "healthy"}), 200

# ======================= RESTful API Routes ====================

@app.route('/api/businesses', methods=['GET'])
def get_businesses() -> Response:
    """
    RESTful endpoint: GET /api/businesses
    """
    # Extract query parameters
    search_query = request.args.get('search', type=str)
    category = request.args.get('category', type=str)
    filepath = request.args.get('filepath', 'data/businesses.json', type=str)
    radius = request.args.get('radius', 10, type=int)
    lat1 = request.args.get('lat1', type=float)
    lon1 = request.args.get('lon1', type=float)

    try:
        # Start with all businesses
        results = jh.load_businesses(input_filepath=filepath)

        # Apply radius filter first if provided
        if lat1 and lon1:
            if radius != 0:
                results = bm.filter_by_radius(results, radius, lat1, lon1)
            else:
                resp = jsonify({"error": "Radius must be nonzero"})
                return make_response(resp, 500)

        # Apply category filter if provided
        if category:
            results = bm.filter_by_category(results, category)

        # Apply search filter if provided (fuzzy matching)
        if search_query:
            results = bm.search_by_name(results, search_query)

        resp = jsonify({
            "businesses": results,
            "count": len(results)
        })
        return make_response(resp, 200)

    except ValueError as e:
        # Handle not found errors from business_manager
        resp = jsonify({"error": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        # Handle unexpected errors
        resp = jsonify({"error": "Internal server error"})
        return make_response(resp, 500)

@app.route('/api/businesses/<int:business_id>', methods=['GET'])
def get_business_by_id(business_id: int) -> Response:
    """
    RESTful endpoint: GET /api/businesses/<id>

    Returns a single business by its ID.

    Example:
    - /api/businesses/123456
    """
    results = jh.load_businesses()
    try:
        results = bm.search_by_id(results, business_id=business_id)

        # Return the first (and should be only) result
        resp = jsonify({
            "business": results[0] if results else None,
        })
        return make_response(resp, 200)

    except ValueError as e:
        # Business not found
        resp = jsonify({"error": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        # Unexpected error
        resp = jsonify({"error": "Internal server error"})
        return make_response(resp, 500)

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
