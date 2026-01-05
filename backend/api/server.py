"""
./backend/api/server.py

Entry point for web API. The main file that ties everything together.
"""

import sys
import os
from typing import Union, Tuple, Any, Literal

from flask import Flask, Response, jsonify, request, make_response
from flask_cors import CORS

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import backend.core.business_manager as bm

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

# ======================= Routing blueprints ====================

@app.route('/api/businesses/get_businesses', methods=['GET'])
def get_businesses() -> Response:
    """
    Getting all businesses from JSON file.
    """
    filepath = request.args.get('filepath', 'data/businesses.json')
    results = bm.get_all_businesses(filepath=filepath)
    resp = jsonify({
        "results": results,
        "count": len(results)
        })
    return make_response(resp, 200)

@app.route('/api/businesses/id_search', methods=['GET'])
def id_search() -> Response:
    """
    Returns the business matching the ID.
    """
    business_id = request.args.get('business_id', type=int)

    if business_id is None:
        resp = jsonify({"error": "Business ID is required and must be an integer"})
        return make_response(resp, 400)

    results = bm.search_by_id(business_id=business_id)
    resp = jsonify({
        "results": results,
        "count": len(results)
        })
    return make_response(resp, 200)

@app.route('/api/businesses/name_search', methods=['GET'])
def name_search() -> Response:
    """
    Searches businesses by name using fuzzy matching to account for user typos.
    """
    name = request.args.get('name', type=str)

    if name is None:
        resp = jsonify({"error": "Name is required and must be a string"})
        return make_response(resp, 400)

    results = bm.search_by_name(name)
    resp = jsonify({
        "results": results,
        "count": len(results)
        })
    return make_response(resp, 200)

@app.route('/api/businesses/category_filter', methods=['GET'])
def category_filter() -> Response:
    """
    Filters through businesses by category.
    """
    category = request.args.get('category', type=str)

    if category is None:
        resp = jsonify({"error": "Category is required and must be a string"})
        return make_response(resp, 400)

    results = bm.filter_by_category(category=category)
    resp = jsonify({
        "results": results,
        "count": len(results)
        })
    return make_response(resp, 200)