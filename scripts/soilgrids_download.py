#!/usr/bin/env python3
"""
SoilGrids Data Download CLI
===========================
Query and download ISRIC SoilGrids soil property data.

Privacy Notice:
- This tool sends ONLY the following data to rest.isric.org:
  * Latitude/longitude or bounding box coordinates
  * Property names
  * Depth intervals
- NO personal data, credentials, or device information is sent.
- All data is processed locally except the API request itself.

License: MIT-0 (Public Domain)
Data: ISRIC SoilGrids, CC-BY 4.0
"""

import argparse
import csv
import json
import sys
import os
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests>=2.28.0")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# ── Constants ──────────────────────────────────────────────────────────────────
API_BASE = "https://rest.isric.org/soilgrids/v2.0"
PROFILES_ENDPOINT = f"{API_BASE}/profiles"
LAYERS_ENDPOINT = f"{API_BASE}/layers"

COMMON_PROPERTIES = {
    "phh2o": {"label": "Soil pH in H2O", "unit": "pH x10"},
    "soc": {"label": "Soil Organic Carbon", "unit": "g/kg"},
    "sand": {"label": "Sand fraction", "unit": "g/kg"},
    "silt": {"label": "Silt fraction", "unit": "g/kg"},
    "clay": {"label": "Clay fraction", "unit": "g/kg"},
    "bdv": {"label": "Bulk Density (fine earth)", "unit": "cg/cm³"},
    "cec": {"label": "Cation Exchange Capacity", "unit": "mmol(c)/kg"},
    "nitrogen": {"label": "Total Nitrogen", "unit": "g/kg"},
    "ocs": {"label": "Organic Carbon Stock", "unit": "t/ha"},
    "wv0010": {"label": "Volumetric Water Content at 10 kPa", "unit": "cm³/cm³"},
    "wv0033": {"label": "Volumetric Water Content at 33 kPa", "unit": "cm³/cm³"},
    "wv1500": {"label": "Volumetric Water Content at 1500 kPa", "unit": "cm³/cm³"},
    "cfvo": {"label": "Coarse Fragments Volumetric", "unit": "cm³/dm³"},
}

DEPTH_LAYERS = [
    "0-5cm",
    "5-15cm",
    "15-30cm",
    "30-60cm",
    "60-100cm",
    "100-200cm",
]

# ── Validation ─────────────────────────────────────────────────────────────────
def validate_latlon(lat, lon):
    """Validate latitude and longitude values."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

def validate_bbox(bbox):
    """Validate bounding box: west, south, east, north."""
    if len(bbox) != 4:
        raise ValueError("Bounding box must have 4 values: west south east north")
    west, south, east, north = bbox
    validate_latlon(south, west)
    validate_latlon(north, east)
    if south >= north:
        raise ValueError(f"South ({south}) must be less than North ({north})")
    if west >= east:
        raise ValueError(f"West ({west}) must be less than East ({east})")
    return west, south, east, north

def validate_depths(depths):
    """Validate depth layer names."""
    valid = []
    for d in depths:
        d = d.strip()
        if d not in DEPTH_LAYERS:
            raise ValueError(f"Unknown depth layer: '{d}'. Valid: {', '.join(DEPTH_LAYERS)}")
        valid.append(d)
    return valid

# ── API Functions ──────────────────────────────────────────────────────────────
def fetch_soilgrids_point(properties, lat, lon, depths=None):
    """Fetch soil data for a single point."""
    params = {
        "lon": lon,
        "lat": lat,
    }

    if depths:
        params["depth"] = ",".join(depths)

    try:
        resp = requests.get(PROFILES_ENDPOINT, params=params, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Try fewer properties or check your connection.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Connection error. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error {resp.status_code}: {resp.text[:300]}")

    return resp.json()

def parse_point_response(data, properties, lat, lon):
    """Parse SoilGrids point response into records."""
    records = []

    if "properties" not in data:
        raise RuntimeError(f"Unexpected response format. Keys: {list(data.keys())}")

    props = data["properties"]
    layers = props.get("layers", [])

    if not layers:
        print("Warning: No layer data returned. The location may be over water or outside coverage.")
        return records

    for layer in layers:
        layer_name = layer.get("name", "unknown")
        depths_data = layer.get("depths", [])

        for depth_info in depths_data:
            record = {
                "latitude": lat,
                "longitude": lon,
                "property": layer_name,
                "depth": depth_info.get("label", "unknown"),
                "unit": layer.get("unit_measure", {}).get("mapped_units", "unknown"),
            }

            # Extract mean value
            values = depth_info.get("values", {})
            record["mean"] = values.get("mean")
            record["Q0.05"] = values.get("Q0.05")
            record["Q0.5"] = values.get("Q0.5")
            record["Q0.95"] = values.get("Q0.95")

            records.append(record)

    return records

def fetch_soilgrids_bbox(properties, bbox, depths=None):
    """Fetch soil data for a bounding box (returns grid info)."""
    west, south, east, north = bbox

    # SoilGrids bbox query uses the same endpoint with bbox parameter
    params = {
        "west": west,
        "south": south,
        "east": east,
        "north": north,
    }

    if depths:
        params["depth"] = ",".join(depths)

    try:
        resp = requests.get(PROFILES_ENDPOINT, params=params, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Try a smaller bbox or fewer properties.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Connection error. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error {resp.status_code}: {resp.text[:300]}")

    return resp.json()

# ── Output Functions ───────────────────────────────────────────────────────────
def write_csv(records, output_path):
    """Write records to CSV file."""
    if not records:
        print("Warning: No data to write.")
        return

    fieldnames = list(records[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Written {len(records)} records to {output_path}")

def write_json(records, output_path, metadata=None):
    """Write records to JSON file."""
    output = {
        "metadata": metadata or {},
        "count": len(records),
        "data": records,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Written {len(records)} records to {output_path}")

# ── CLI Commands ───────────────────────────────────────────────────────────────
def cmd_query(args):
    """Query soil property data."""
    properties = [p.strip() for p in args.property.split(",")]
    depths = validate_depths(args.depth) if args.depth else None

    # Validate spatial input
    if args.lat is not None and args.lon is not None:
        validate_latlon(args.lat, args.lon)
        lat, lon = args.lat, args.lon
    elif args.bbox:
        west, south, east, north = validate_bbox(args.bbox)
        # Use center for point query
        lat = (south + north) / 2
        lon = (west + east) / 2
        print(f"Note: Using center of bbox ({lat:.4f}, {lon:.4f}) for point query.")
        print("      SoilGrids API returns point data; bbox is used for center point only.")
    else:
        print("Error: Provide either --lat/--lon or --bbox")
        sys.exit(1)

    # Fetch data
    print(f"Querying SoilGrids for: {', '.join(properties)}")
    print(f"  Location: ({lat:.4f}, {lon:.4f})")
    if depths:
        print(f"  Depths: {', '.join(depths)}")

    data = fetch_soilgrids_point(properties, lat, lon, depths)
    records = parse_point_response(data, properties, lat, lon)

    if not records:
        print("No data returned.")
        sys.exit(1)

    # Output
    output_path = args.output
    if args.format == "json" or output_path.endswith(".json"):
        metadata = {
            "source": "ISRIC SoilGrids v2.0",
            "api": API_BASE,
            "properties": properties,
            "latitude": lat,
            "longitude": lon,
            "resolution": "250m",
        }
        write_json(records, output_path, metadata)
    else:
        write_csv(records, output_path)

def cmd_list_properties(args):
    """List available soil properties."""
    print("=" * 70)
    print("SoilGrids - Common Properties")
    print("=" * 70)
    print(f"{'Property':<15} {'Label':<40} {'Unit'}")
    print("-" * 70)
    for prop, info in COMMON_PROPERTIES.items():
        print(f"{prop:<15} {info['label']:<40} {info['unit']}")
    print("-" * 70)
    print(f"\nTotal: {len(COMMON_PROPERTIES)} common properties shown.")
    print("Full list: https://www.isric.org/explore/soilgrids/faq-soilgrids")

def cmd_list_depths(args):
    """List available depth layers."""
    print("=" * 50)
    print("SoilGrids - Standard Depth Layers")
    print("=" * 50)
    for depth in DEPTH_LAYERS:
        print(f"  {depth}")
    print("-" * 50)
    print(f"Total: {len(DEPTH_LAYERS)} standard depth layers")
    print("Resolution: 250m")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="soilgrids-download",
        description="Query and download ISRIC SoilGrids soil property data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s query --property phh2o --lat 39.9042 --lon 116.4074 \\
    --output beijing_ph.csv

  %(prog)s query --property phh2o,soc,sand,silt,clay \\
    --bbox 73 18 135 54 --depth 0-5,5-15 \\
    --output china_soil.json --format json

  %(prog)s list-properties
  %(prog)s list-depths
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Query command
    q = subparsers.add_parser("query", help="Query soil property data")
    q.add_argument("--property", default="phh2o",
                   help="Comma-separated property names (default: phh2o)")
    q.add_argument("--lat", type=float, help="Latitude (-90 to 90)")
    q.add_argument("--lon", type=float, help="Longitude (-180 to 180)")
    q.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"),
                   help="Bounding box: west south east north")
    q.add_argument("--depth", type=lambda s: [d.strip() for d in s.split(",")],
                   help="Comma-separated depth layers (default: all)")
    q.add_argument("--output", default="soilgrids_data.csv",
                   help="Output file path (default: soilgrids_data.csv)")
    q.add_argument("--format", choices=["csv", "json"], default="csv",
                   help="Output format (default: csv)")
    q.set_defaults(func=cmd_query)

    # List properties command
    lp = subparsers.add_parser("list-properties", help="List available soil properties")
    lp.set_defaults(func=cmd_list_properties)

    # List depths command
    ld = subparsers.add_parser("list-depths", help="List available depth layers")
    ld.set_defaults(func=cmd_list_depths)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except ValueError as e:
        print(f"Validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)

if __name__ == "__main__":
    main()
