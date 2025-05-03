"""
Polygonal NFC Coil DXF Generator
--------------------------------

This script generates a planar spiral NFC antenna coil based on an N-sided regular polygon and
exports the layout as a DXF file. It also visualizes the coil using matplotlib and calculates
its total trace resistance based on geometry and copper properties.

Key Features:
- Parametric design: outer/inner diameter, trace width, spacing, thickness, number of sides, number of turns.
- Generates spiral coils using regular polygons (hexagon by default, but configurable to any side count).
- Two layout styles to accommodate initial turn spacing methods.
- Outputs DXF using `ezdxf` with metric units (mm).
- Visualizes coil geometry with matplotlib.
- Calculates DC resistance using total segment length and copper trace dimensions.

Applications:
- NFC / RFID antenna layout
- Planar inductors and wireless power coils
- Custom PCB coil design and analysis

References:
- TranslatorsCafe Planar Coil Inductance Calculator:
  https://www.translatorscafe.com/unit-converter/sq/calculator/planar-coil-inductance/
- Circuits.dk Planar Inductor Calculator:
  https://www.circuits.dk/calculator_planar_coil_inductor.htm

Dependencies:
- Python 3.x
- ezdxf
- matplotlib

Usage Example:
---------------
coordinates = generate_hexagon_nfc_coil_dxf(
    outer_diameter_mm=30.0,
    inner_diameter_mm=25.0,
    trace_width_mm=0.2,
    trace_thickness_mm=0.035,
    spacing_mm=0.25,
    num_turns=7,
    num_sides=6,
    style=1
)

plot_hexagon_nfc_coil(coordinates)

Author: Marcus Lechner
Date: April 2025
"""

import math
import ezdxf
import matplotlib.pyplot as plt
import os


def generate_hexagon_nfc_coil_dxf(
    outer_diameter_mm=31.5,
    inner_diameter_mm=25.2,
    trace_width_mm=0.3,
    trace_thickness_mm=0.035,
    spacing_mm=0.3,
    num_turns= 7,
    num_sides = 6,
    style = 1,  
):
    
    """
    Generate a polygonal planar NFC coil and save it as a DXF file.

    :param outer_diameter_mm: Outer flat-to-flat diameter of the coil (inscribed) in mm
    :param inner_diameter_mm: Inner flat-to-flat diameter of the coil (inscribed) in mm
    :param trace_width_mm: Width of the copper trace in mm
    :param trace_thickness_mm: Thickness of the copper trace in mm
    :param spacing_mm: Spacing between coil turns in mm
    :param num_turns: Number of turns in the coil
    :param num_sides: Number of polygon sides (e.g. 6 = hexagon, 100 ≈ circle)
    :param style: Turn layout style (0 = segment-by-segment shrink, 1 = radial shrink per turn)
    :return: List of coordinate points for each turn

    Output:
    - Saves a DXF file in the script's directory with parameters in the filename
    """
 

    filename = f"hexagon_nfc_coil_OD{outer_diameter_mm}_TW{trace_width_mm}_SP{spacing_mm}_NT{num_turns}_NS{num_sides}_ST{style}.dxf"

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create the full path for the DXF file in the same directory as the script
    full_path = os.path.join(script_dir, filename)

    # Setup DXF file with millimeter units
    doc = ezdxf.new(dxfversion='AC1027')  # DXF version
    doc.header['$INSUNITS'] = 4  # Set units to millimeters
    msp = doc.modelspace()

    degree = 180/num_sides

    # conversion from inscribed dimension to circumscribed
    outer_diameter_mm = outer_diameter_mm / math.cos(math.radians(degree))

    # accomodate for first turn shrinkage in style 0:
    if(style == 0):
        outer_diameter_mm = outer_diameter_mm + trace_width_mm + spacing_mm

    # Constants
    delta_r = trace_width_mm / math.cos(math.radians(degree)) + spacing_mm / math.cos(math.radians(degree))  # How much to shrink per turn
    r_outer = (outer_diameter_mm - (trace_width_mm / math.cos(math.radians(degree))))/2 # Outer radius

    angles_deg = []
    angle_per_section = 360 / num_sides
    for side in range(num_sides):
        angles_deg.append(angle_per_section * side)
    # angles_deg = [0, 60, 120, 180, 240, 300] #0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300]  # Hexagon angles

    all_coordinates = []
    r_current = r_outer
    points = []

    # Draw each turn
    for turn in range(num_turns):

        for angle_deg in angles_deg:
            angle_rad = math.radians(angle_deg)
            if(style == 0):
                r_current = r_current - (delta_r/6)
            x = (r_current) * math.cos(angle_rad)
            y = (r_current) * math.sin(angle_rad)
            points.append((x, y))
            
        # decrease diameter every turn
        if(style == 1):
            r_current = r_current - delta_r

    if(style == 0):
        r_current = r_current - (delta_r/6)

    #add last point    
    angle_rad = math.radians(0)
    x = (r_current) * math.cos(angle_rad)
    y = (r_current) * math.sin(angle_rad)
    points.append((x, y))
        
    # Save coordinates
    all_coordinates.append(points)
    
    # Draw polyline
    msp.add_lwpolyline(points, close=False)

    #save DXF file
    doc.saveas(full_path)
    print(f"DXF saved as: {full_path}")
    
    # Calculate resistance
    resistivity_copper = 1.70e-8  # Ohm-meter for copper
    resistance = calculate_coil_resistance(trace_width_mm, trace_thickness_mm, resistivity_copper, all_coordinates)
    print(f"\nTotal coil resistance: {resistance:.6f} Ohms")

    return all_coordinates


# Visualize using matplotlib
def plot_hexagon_nfc_coil(all_coordinates):
    plt.figure(figsize=(6, 6))
    
    for points in all_coordinates:
        # Unzip the list of points into x and y coordinates
        x, y = zip(*points)
        plt.plot(x, y, marker='o')

    plt.axis('equal')
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.title("Hexagonal NFC Coil")
    plt.grid(True)
    plt.show()


def calculate_coil_resistance(trace_width_mm, trace_thickness_mm, resistivity_copper, coordinates):
    """
    Calculate the total resistance of the coil.

    :param trace_width_mm: Trace width in mm
    :param trace_thickness_mm: Trace thickness in mm
    :param resistivity_copper: Resistivity of copper in ohm-meter (default: 1.68e-8)
    :param coordinates: List of coordinates for all the turns in the coil
    :return: Total resistance in ohms
    """
    # Convert dimensions from mm to meters
    trace_width_m = trace_width_mm / 1000
    trace_thickness_m = trace_thickness_mm / 1000

    # Calculate the cross-sectional area of the trace
    area = trace_width_m * trace_thickness_m  # in square meters

    # Sum of the lengths of all segments
    total_length_mm = 0.0
    for turn_coordinates in coordinates:
        # Calculate the length of each segment in the turn
        for i in range(len(turn_coordinates) - 1):
            x1, y1 = turn_coordinates[i]
            x2, y2 = turn_coordinates[i + 1]
            segment_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)  # Euclidean distance
            total_length_mm += segment_length
    print(f"Total length in mm: {total_length_mm}")
    # Convert dimensions from mm to meters
    total_length_m = total_length_mm /1000
    

    # Calculate the resistance using R = ρ * L / A
    resistance = resistivity_copper * total_length_m / area
    return resistance

# Visualize coil with matplotlib
coordinates = generate_hexagon_nfc_coil_dxf()
plot_hexagon_nfc_coil(coordinates)

