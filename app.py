"""
Flask Backend for Pune Women's Safety Map
==========================================
Serves crime data via REST API.

Usage:
    python app.py

Endpoints:
    GET /api/crimes          - All crime data
    GET /api/crimes?area=X   - Filter by area
    GET /api/crimes?type=X   - Filter by crime type
    GET /api/stats            - Aggregated statistics
    GET /api/areas            - List of all areas
    GET /api/types            - List of crime types
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import json
import os

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for frontend access

DATA_FILE = 'data.json'


def load_data():
    """Load crime data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []


def get_aggregated_stats(data):
    """Calculate aggregated statistics."""
    if not data:
        return {
            "total_crimes": 0,
            "total_areas": 0,
            "crime_types": {},
            "top_areas": [],
            "highest_risk_area": None
        }

    # Total crimes
    total = sum(record['crime_count'] for record in data)

    # Unique areas
    areas = set(record['area'] for record in data)

    # Crime type totals
    type_totals = {}
    for record in data:
        ct = record['crime_type']
        type_totals[ct] = type_totals.get(ct, 0) + record['crime_count']

    # Area totals
    area_totals = {}
    for record in data:
        area = record['area']
        area_totals[area] = area_totals.get(area, 0) + record['crime_count']

    # Top 5 areas
    top_areas = sorted(area_totals.items(), key=lambda x: -x[1])[:5]

    # Highest risk area
    highest_risk = max(area_totals.items(), key=lambda x: x[1]) if area_totals else None

    return {
        "total_crimes": total,
        "total_areas": len(areas),
        "crime_types": type_totals,
        "top_areas": [{"area": a, "count": c} for a, c in top_areas],
        "highest_risk_area": {"area": highest_risk[0], "count": highest_risk[1]} if highest_risk else None
    }


# ============================================================
# API Endpoints
# ============================================================

@app.route('/api/crimes', methods=['GET'])
def get_crimes():
    """Get all crime data with optional filtering."""
    data = load_data()

    # Filter by area
    area = request.args.get('area')
    if area:
        data = [r for r in data if r['area'].lower() == area.lower()]

    # Filter by crime type
    crime_type = request.args.get('type')
    if crime_type:
        data = [r for r in data if r['crime_type'] == crime_type]

    # Filter by year
    year = request.args.get('year')
    if year:
        data = [r for r in data if r['year'] == int(year)]

    return jsonify({
        "success": True,
        "count": len(data),
        "data": data
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get aggregated statistics."""
    data = load_data()
    stats = get_aggregated_stats(data)
    return jsonify({
        "success": True,
        "data": stats
    })


@app.route('/api/areas', methods=['GET'])
def get_areas():
    """Get list of all areas."""
    data = load_data()
    areas = sorted(set(record['area'] for record in data))
    return jsonify({
        "success": True,
        "count": len(areas),
        "data": areas
    })


@app.route('/api/types', methods=['GET'])
def get_types():
    """Get list of crime types."""
    return jsonify({
        "success": True,
        "data": [
            {"type": "domestic_violence", "label": "Domestic Violence", "description": "Cruelty by Husband/Relatives"},
            {"type": "assault", "label": "Assault", "description": "Assault on Women with intent to outrage modesty"},
            {"type": "harassment", "label": "Harassment", "description": "Sexual Harassment, Eve Teasing"},
            {"type": "stalking", "label": "Stalking", "description": "Stalking cases"},
            {"type": "dowry_deaths", "label": "Dowry Deaths", "description": "Dowry Deaths (Sec. 304B IPC)"},
            {"type": "other", "label": "Other", "description": "Acid Attack, Kidnapping, etc."}
        ]
    })


@app.route('/api/search', methods=['GET'])
def search():
    """Search areas by name (partial match)."""
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify({"success": True, "data": []})

    data = load_data()
    areas = set(record['area'] for record in data)
    matches = [a for a in areas if query in a.lower()]

    return jsonify({
        "success": True,
        "query": query,
        "data": matches
    })


# ============================================================
# Static Files (for development)
# ============================================================

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('.', filename)


# ============================================================
# Data Update Endpoint (for future use)
# ============================================================

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """
    Regenerate data.json using process_data.py
    This would be called when new NCRB data is released.
    """
    try:
        # Import and run the processor
        import process_data
        # The processor writes directly to data.json
        return jsonify({
            "success": True,
            "message": "Data refreshed successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# ML Prediction Endpoint (placeholder for future)
# ============================================================

@app.route('/api/predict', methods=['GET'])
def predict():
    """
    Predict risk level for an area.
    Placeholder for ML model integration.
    """
    area = request.args.get('area')
    if not area:
        return jsonify({"success": False, "error": "Area parameter required"}), 400

    data = load_data()
    area_records = [r for r in data if r['area'].lower() == area.lower()]

    if not area_records:
        return jsonify({"success": False, "error": "Area not found"}), 404

    total = sum(r['crime_count'] for r in area_records)

    # Simple risk calculation
    if total >= 150:
        risk_level = "HIGH"
    elif total >= 80:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return jsonify({
        "success": True,
        "data": {
            "area": area,
            "total_crimes": total,
            "risk_level": risk_level,
            "crime_breakdown": {r['crime_type']: r['crime_count'] for r in area_records}
        }
    })


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print("=" * 50)
    print("Pune Women's Safety Map - Flask API")
    print("=" * 50)
    print("\nEndpoints:")
    print("  GET /                    - Main page")
    print("  GET /api/crimes          - Crime data")
    print("  GET /api/stats           - Statistics")
    print("  GET /api/areas           - List areas")
    print("  GET /api/types           - Crime types")
    print("  GET /api/search?q=X      - Search areas")
    print("  GET /api/predict?area=X  - Predict risk")
    print("\nRunning on http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
