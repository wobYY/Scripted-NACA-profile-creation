import os
import sys
import pandas as pd
from utils.logging import get_logger

# Setup the logger
log = get_logger("snpc", "DEBUG")

# Setup the FreeCAD import
# It's possible to do both on Windows and Linux
# But it's easier to do it on Linux
# Docs: https://wiki.freecad.org/Embedding_FreeCAD
freecad_path = "/usr/lib/freecad-python3/lib/"
sys.path.append(freecad_path)
import FreeCAD  # Import FreeCAD after adding the path
import FreeCADGui  # Import FreeCADGui after adding the path
from FreeCAD import Base

# Because PartDesign is not imported by default with the imports above
# We need to import the module folder for PartDesign
# Forum: https://forum.freecad.org/viewtopic.php?style=4&p=677043#p677043
sys.path.append("/usr/lib/freecad/Mod")
import PartDesign  # Import PartDesign after adding the Mod path


# Function to draw the profile from the csv
def draw_from_csv_coordinates(name, coordinates, **kwargs):
    # Make sure that the "coordinates" variable is a dataframe
    if not isinstance(coordinates, pd.DataFrame):
        log.error("The coordinates variable is not a dataframe")
        raise TypeError("The coordinates variable is not a dataframe")

    # Check if the dataframe has the correct columns
    if not "x" in coordinates.columns or not "y" in coordinates.columns:
        log.error("The dataframe doesn't have the correct columns")
        raise ValueError("The dataframe doesn't have the correct columns")

    # Check the type of values in the dataframe and convert them to floats
    log.debug("Checking the type of values in the dataframe")
    if coordinates["x"].dtype != float:
        log.debug("Converting the x values to floats")
        coordinates["x"] = coordinates["x"].astype(float)
    if coordinates["y"].dtype != float:
        log.debug("Converting the y values to floats")
        coordinates["y"] = coordinates["y"].astype(float)

    # Ask the user if they want to scale the profile
    # If they do, ask them for the scale factor
    # If they don't, set the scale factor to 1
    log.debug("Checking if the user wants to scale the profile")
    scale_factor = 1
    if input(f"Do you want to scale the {name} profile? (y/n): ").lower() == "y":
        log.debug("User wants to scale the profile")
        scale_factor = float(input("Enter the scale factor: "))
        log.debug("Scale factor set to: %s", scale_factor)
        coordinates["x"] = coordinates["x"] * scale_factor
        coordinates["y"] = coordinates["y"] * scale_factor
        log.debug("Profile scaled")

    # Check if "cad" folder exists, if it doesn't create it
    log.debug("Checking if cad folder exists")
    if not os.path.exists(f"{cwd}/cad"):
        log.debug("cad folder doesn't exist, creating it")
        os.mkdir(f"{cwd}/cad")
        log.debug("cad folder created")

    # Create a new document
    log.debug("Creating a new document")
    document = App.newDocument()
    log.debug("Document created, preparing to save as %s.FCStd", name)
    # If the document already exists, delete the existing document
    if os.path.exists(f"{cwd}/cad/{name}.FCStd"):
        log.debug("Document already exists, deleting the existing document")
        os.remove(f"{cwd}/cad/{name}.FCStd")
        log.debug("Existing document deleted")

    # Add a new body to the document
    log.debug("Adding a new body to the document")
    document.addObject("PartDesign::Body", "Body")
    document.recompute()
    log.debug("Body added to the document")

    # Rename the body
    # Remove any whitespaces from the "name" variable
    # Replace any symbols with underscores
    log.debug("Ensuring the body name is valid")
    body_name = name.replace(" ", "_").replace("-", "_")
    log.debug("Setting the body name to: %s", body_name)
    document.getObject("Body").Label = body_name
    document.recompute()
    log.debug("Body name set to: %s", body_name)

    # For the Body add a sketch in teh YZ plane
    document.getObject("Body").newObject("Sketcher::SketchObject", "Sketch")
    document.getObject("Sketch").Support = (
        document.getObject("YZ_Plane"),
        [""],
    )
    document.getObject("Sketch").MapMode = "FlatFace"
    document.recompute()

    # Check how many x coordinates there are in the dataframe
    number_of_coord = coordinates["x"].count()
    log.debug("Number of coordinates: %s", number_of_coord)

    # Create Points for each coordinate
    # for x, y in coordinates in the "coordinates" dataframe
    log.debug("Checking the coordinates dataframe")
    V = Base.Vector
    poles = []  # Poles for the B-spline
    for x, y in zip(coordinates["x"], coordinates["y"]):
        log.debug("x: %s | y: %s", f"{x:<6}", f"{y:<6}")
        # document.getObject("Sketch").addGeometry(
        #     Part.Point(App.Vector(float(x), float(y), 0))
        # )
        # document.recompute()
        poles.append(V(float(x), float(y)))

    # Draw a B-spline by knots through the points
    # Docs: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/BSplineCurve_API.md
    log.debug("Drawing B-Spline")
    b_spline = Part.BSplineCurve()
    b_spline.buildFromPoles(poles)
    document.getObject("Sketch").addGeometry(b_spline)
    document.recompute()
    log.debug("B-Spline drawn")

    # Connect the first and last point with a straight line
    log.debug("Connecting the first and last point with a straight line")
    closing_line = Part.LineSegment(poles[0], poles[-1])
    document.getObject("Sketch").addGeometry(closing_line)
    log.debug("Profile closed with a straight line")

    # Creating the domain around the profile
    log.info("Profile created, creating the domain around the profile")

    # Get the minimum and maximum x and y coordinates
    log.debug("Getting the minimum and maximum x and y coordinates")
    min_x = coordinates["x"].min()
    max_x = coordinates["x"].max()
    min_y = coordinates["y"].min()
    max_y = coordinates["y"].max()
    log.debug("Minimum x: %s | Maximum x: %s", f"{min_x:<6}", f"{max_x:<6}")
    log.debug("Minimum y: %s | Maximum y: %s", f"{min_y:<6}", f"{max_y:<6}")

    # Calculating the length of the profile
    log.debug("Calculating the length of the profile")
    length = max_x - min_x

    # Calculating the dimensions for the domain
    log.debug("Calculating the dimensions for the domain")
    x_front = min_x - (length * 3)  # 3x the profile length for the flow to develop
    x_back = max_x + (length * 7)  # 7x the profile length
    y_above = max_y + (length * 3)  # 3x the profile length
    y_below = min_y - (length * 3)  # 3x the profile length

    # Draw the domain
    log.debug("Drawing the domain")
    document.getObject("Sketch").addGeometry(
        Part.LineSegment(V(x_front, y_above, 0), V(x_back, y_above, 0))
    )  # Top line
    document.getObject("Sketch").addGeometry(
        Part.LineSegment(V(x_back, y_above, 0), V(x_back, y_below, 0))
    )  # Right line
    document.getObject("Sketch").addGeometry(
        Part.LineSegment(V(x_back, y_below, 0), V(x_front, y_below, 0))
    )  # Bottom line
    document.getObject("Sketch").addGeometry(
        Part.LineSegment(V(x_front, y_below, 0), V(x_front, y_above, 0))
    )  # Left line
    document.recompute()
    log.info("Domain created, profile ready to be extruded")

    # Save the new document
    document.saveAs(f"{cwd}/cad/{name}.FCStd")
    log.debug("Document saved as %s.FCStd", name)


# Get the current working directory
cwd = os.getcwd()

for file in os.listdir(cwd + "/profiles"):
    log.info("Checking for all text files in the /profiles folder")
    if file.endswith(".txt"):
        log.debug("Found a .txt file (%s), converting to .csv", file)

        # Open the file
        with open("profiles/" + file, "r") as f:
            lines = f.readlines()

        # If the file contains NACA in the first line remove the first line
        log.debug("Checking if the first line contains NACA")
        if "NACA" in lines[0]:
            log.debug("First line contains NACA, removing the first line")
            lines = lines[1:]

        # Read the file as a dataframe
        log.debug("Storing the file as a dataframe")
        df = pd.DataFrame([line.split() for line in lines], columns=["x", "y"])

        # Remove .txt from the filename
        log.debug("Removing .txt from the filename")
        filename = file[:-4]
        log.debug("Filename: %s", filename)

        # Save the file as a csv
        log.debug("Saving the processed file as a csv")
        df.to_csv(f"profiles/{filename}.csv", index=False, header=False)
        log.info("Saved %s as a csv", filename)

        # Draw the profile from the csv
        log.info("Drawing the profile from coordinates provided in %s.csv", filename)
        draw_from_csv_coordinates(filename, df)
