"""
Pune Women's Safety Data Processor (v2)
=========================================
Uses actual NCRB 2023 data for Pune totals + estimated distributions.

Data Sources:
- Total Pune crimes: NCRB City-wise XLSX (VERIFIED: 2,550 cases in 2023)
- Crime type proportions: NCRB Crime Head-wise PDF (estimated from Maharashtra patterns)
- Area distribution: Estimated based on population density (approximate)

Usage:
    python process_data.py
"""

import json
import hashlib

# ============================================================
# VERIFIED DATA FROM NCRB 2023
# ============================================================

# Source: NCRB "City-wise Cases Registered under Crimes against Women - 2023"
# Downloaded from: data.opencity.in
# Pune total: 2,550 cases (row 40 in the dataset)
PUNE_TOTAL_CRIMES_2023 = 2550

# ============================================================
# CRIME TYPE DISTRIBUTION (Based on NCRB Maharashtra patterns)
# ============================================================
# These proportions are typical for Maharashtra based on NCRB reports:
# - Domestic Violence (Cruelty by Husband): ~40%
# - Assault on Women: ~25%
# - Harassment (including sexual): ~20%
# - Stalking: ~8%
# - Dowry Deaths: ~5%
# - Others (acid attack, kidnapping, etc.): ~2%

CRIME_TYPE_PROPORTIONS = {
    "domestic_violence": 0.40,  # Cruelty by Husband/Relatives
    "assault": 0.25,           # Assault on Women with intent to outrage modesty
    "harassment": 0.20,        # Sexual Harassment, Eve Teasing, etc.
    "stalking": 0.08,          # Stalking
    "dowry_deaths": 0.05,      # Dowry Deaths (included as assault)
    "other": 0.02             # Acid attack, kidnapping, etc.
}

# ============================================================
# PUNE AREAS WITH COORDINATES
# ============================================================
# Areas with approximate centroids (for visualization only)
# Source: Google Maps coordinates for area centroids

PUNE_AREAS = {
    "Hadapsar":        {"lat": 18.5193, "lng": 73.9423, "pop_factor": 1.2},
    "Kondhwa":         {"lat": 18.4912, "lng": 73.9278, "pop_factor": 1.1},
    "Wanowrie":        {"lat": 18.4873, "lng": 73.9021, "pop_factor": 0.9},
    "Bibvewadi":       {"lat": 18.4756, "lng": 73.8765, "pop_factor": 1.0},
    "Swargate":        {"lat": 18.5023, "lng": 73.8567, "pop_factor": 1.3},  # Commercial hub
    "Shivaji Nagar":   {"lat": 18.5306, "lng": 73.8447, "pop_factor": 1.4}, # High density
    "Ganesh Peth":     {"lat": 18.5156, "lng": 73.8628, "pop_factor": 1.1},
    "Dhole Patil Rd":  {"lat": 18.5312, "lng": 73.8689, "pop_factor": 1.0},
    "Kothrud":         {"lat": 18.5095, "lng": 73.8075, "pop_factor": 0.8},  # Suburban
    "Aundh":           {"lat": 18.5745, "lng": 73.8187, "pop_factor": 0.7},
    "Baner":           {"lat": 18.5594, "lng": 73.8076, "pop_factor": 0.9},
    "Wakad":           {"lat": 18.5981, "lng": 73.7647, "pop_factor": 1.0},
    "Hinjewadi":       {"lat": 18.5989, "lng": 73.7387, "pop_factor": 1.1},  # IT hub
    "Viman Nagar":     {"lat": 18.5679, "lng": 73.9144, "pop_factor": 1.0},
    "Khadki":          {"lat": 18.5640, "lng": 73.8768, "pop_factor": 0.9},
    "Yerawada":        {"lat": 18.5479, "lng": 73.8774, "pop_factor": 0.9},
    "Koregaon Park":   {"lat": 18.5362, "lng": 73.8957, "pop_factor": 1.0},
    "Fatima Nagar":    {"lat": 18.5089, "lng": 73.8789, "pop_factor": 0.8},
    "Tingre Nagar":    {"lat": 18.5789, "lng": 73.8978, "pop_factor": 0.7},
    "Mundhwa":         {"lat": 18.5345, "lng": 73.9215, "pop_factor": 0.8},
}


def generate_consistent_random(area_name, crime_type, seed_offset=0):
    """Generate deterministic random value based on area + crime combo."""
    hash_input = f"{area_name}_{crime_type}_{seed_offset}"
    hash_val = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
    return (hash_val % 100) / 100.0  # 0.0 to 0.99


def generate_data():
    """Generate data.json with realistic crime distribution."""
    print("=" * 60)
    print("Pune Women's Safety Data Generator")
    print("=" * 60)
    print(f"\nBase Data: NCRB 2023 Pune Total = {PUNE_TOTAL_CRIMES_2023} cases")
    print("\nCrime Type Distribution (estimated from Maharashtra patterns):")
    for ct, prop in CRIME_TYPE_PROPORTIONS.items():
        count = int(PUNE_TOTAL_CRIMES_2023 * prop)
        print(f"  {ct}: {prop*100:.0f}% (~{count} cases)")

    records = []

    for area_name, area_info in PUNE_AREAS.items():
        lat = area_info["lat"]
        lng = area_info["lng"]
        pop_factor = area_info["pop_factor"]

        # Calculate area weight (0.5 to 1.5 based on population)
        area_weight = 0.5 + (pop_factor * 0.8)

        for crime_type, proportion in CRIME_TYPE_PROPORTIONS.items():
            # Calculate expected crimes for this area + crime type
            expected = PUNE_TOTAL_CRIMES_2023 * proportion / len(PUNE_AREAS)

            # Add variation based on area characteristics
            variation = generate_consistent_random(area_name, crime_type, seed_offset=0)
            variation = 0.5 + (variation * 1.0)  # 0.5 to 1.5 multiplier

            # Crime count for this area + crime type
            crime_count = max(1, int(expected * area_weight * variation))

            records.append({
                "area": area_name,
                "latitude": lat,
                "longitude": lng,
                "crime_type": crime_type,
                "crime_count": crime_count,
                "year": 2023
            })

    return records


def main():
    records = generate_data()

    # Write output
    output_file = "data.json"
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)

    print(f"\n" + "=" * 60)
    print("OUTPUT GENERATED")
    print("=" * 60)
    print(f"File: {output_file}")
    print(f"Total records: {len(records)}")

    # Summary by crime type
    print("\nActual Crime Counts (after distribution):")
    type_totals = {}
    for r in records:
        type_totals[r["crime_type"]] = type_totals.get(r["crime_type"], 0) + r["crime_count"]
    for ct, count in sorted(type_totals.items(), key=lambda x: -x[1]):
        print(f"  {ct}: {count}")

    # Summary by area
    print("\nTop 5 Areas by Total Crimes:")
    area_totals = {}
    for r in records:
        area_totals[r["area"]] = area_totals.get(r["area"], 0) + r["crime_count"]
    top_areas = sorted(area_totals.items(), key=lambda x: -x[1])[:5]
    for area, count in top_areas:
        print(f"  {area}: {count}")

    print("\n" + "=" * 60)
    print("IMPORTANT NOTES:")
    print("=" * 60)
    print("""
1. This data uses VERIFIED Pune total (2,550 cases) from NCRB 2023
2. Crime type proportions are ESTIMATED from Maharashtra patterns
3. Area distribution is APPROXIMATE based on population density
4. For precise data, download police-station level data from NCRB
5. This tool is for awareness and visualization purposes
    """)


if __name__ == "__main__":
    main()
