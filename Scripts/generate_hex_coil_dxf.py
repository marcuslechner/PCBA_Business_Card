import math
import ezdxf
import matplotlib.pyplot as plt
import os

def generate_hexagon_nfc_coil_dxf(
    outer_diameter_mm=33.1,
    inner_diameter_mm=25.2,
    trace_width_mm=0.3,
    trace_thickness_mm=0.035,
    spacing_mm=0.3,
    num_turns=7,
    num_sides = 6,
    style = 1,
    
):
 
    # takes inscribed dimension (used in xxxx) and draws circumscribed hexgon 
    # inscribed dimensions are used in both circuits.dk and translatorcafe inductance calculators
    # - https://www.translatorscafe.com/unit-converter/sq/calculator/planar-coil-inductance/
    # - https://www.circuits.dk/calculator_planar_coil_inductor.htm

    filename = f"hexagon_nfc_coil_OD{outer_diameter_mm}_TW{trace_width_mm}_SP{spacing_mm}_NT{num_turns}_ST{style}.dxf"
    # filename="hexagon_nfc_coil.dxf" 
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create the full path for the DXF file in the same directory as the script
    full_path = os.path.join(script_dir, filename)
    # Setup DXF file
    # Setup DXF file with millimeter units
    doc = ezdxf.new(dxfversion='AC1027')  # DXF version
    doc.header['$INSUNITS'] = 4  # Set units to millimeters
    msp = doc.modelspace()

    # conversion from inscribed dimension to circumscribed
    outer_diameter_mm = outer_diameter_mm / math.cos(math.radians(30))

    # accomodate for first turn shrinkage in style 0:
    if(style == 0):
        outer_diameter_mm = outer_diameter_mm + trace_width_mm + spacing_mm

    # Constants
    delta_r = trace_width_mm / math.cos(math.radians(30)) + spacing_mm / math.cos(math.radians(30))  # How much to shrink per turn
    r_outer = (outer_diameter_mm - (trace_width_mm / math.cos(math.radians(30))))/2 # Outer radius

    angles_deg = []
    angle_per_section = 360 / num_sides
    for side in range(num_sides):
        angles_deg.append(angle_per_section * side)
    angles_deg = [0, 60, 120, 180, 240, 300] #0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300, 0, 60, 120, 180, 240, 300]  # Hexagon angles

    all_coordinates = []

    r_current = r_outer
    section = 0
    points = []

    # Draw each turn
    for turn in range(num_turns):

        
        for idx, angle_deg in enumerate(angles_deg):
            angle_rad = math.radians(angle_deg)

            r_previous = r_current
            # decrease diameter every section
            if(style == 0):
                r_current = r_current - (delta_r/6)
            # section = section + 1
            # print(f"section: {section}, difference: {r_current - r_previous}")
            # print(r_current - delta_r/6*idx)
            x = (r_current) * math.cos(angle_rad)
            y = (r_current) * math.sin(angle_rad)
            points.append((x, y))
            

        # decrease diameter every turn
        if(style == 1):
            r_current = r_current - delta_r

                # points.append(points[0])  # Close the loop
        # r_previous = r_current
        # print(f" 6 - current: {r_current}, difference: {r_current - r_previous}")
        # # r_current = r_outer - (turn - 1 * delta_r)


    if(style == 0):
        r_current = r_current - (delta_r/6)

    #add last point    
    angle_rad = math.radians(0)
    x = (r_current) * math.cos(angle_rad)
    y = (r_current) * math.sin(angle_rad)
    points.append((x, y))

    # print(f"Inner Diameter: {x*2 - trace_width_mm}")


        
    # Save coordinates
    all_coordinates.append(points)
    
    # Draw polyline
    msp.add_lwpolyline(points, close=False)

    #save DXF file
    doc.saveas(full_path)
    print(f"DXF saved as: {full_path}")

    # # Print coordinates nicely
    # for idx, hex_points in enumerate(all_coordinates):
    #     print(f"\nTurn {idx + 1}:")
    #     for x, y in hex_points:
    #         print(f"({x:.3f}, {y:.3f})")

    
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
    total_length_m = 0.0
    for turn_coordinates in coordinates:
        # Calculate the length of each segment in the turn
        for i in range(len(turn_coordinates) - 1):
            x1, y1 = turn_coordinates[i]
            x2, y2 = turn_coordinates[i + 1]
            segment_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)  # Euclidean distance
            total_length_m += segment_length
    print(f"Total length in mm: {total_length_m}")
    # Convert dimensions from mm to meters
    total_length_m = total_length_m /1000
    

    # print(total_length_m)
    # Calculate the resistance using R = ρ * L / A
    resistance = resistivity_copper * total_length_m / area
    return resistance

# Visualize coil with matplotlib
coordinates = generate_hexagon_nfc_coil_dxf()
plot_hexagon_nfc_coil(coordinates)

# Example Usage
# generate_hexagon_nfc_coil_dxf()