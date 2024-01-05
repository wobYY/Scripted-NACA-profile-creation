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

# Because PartDesign is not imported by default
# We need to import the module folder for PartDesign
# Forum: https://forum.freecad.org/viewtopic.php?style=4&p=677043#p677043
sys.path.append("/usr/lib/freecad/Mod")
import PartDesign  # Import PartDesign after adding the path


# Function to draw the profile from the csv
def draw_from_csv_coordinates(name, coordinates, **kwargs):
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

    # Create Points for each coordinate
    # for x, y in coordinates in the "coordinates" dataframe
    log.debug("Checking the coordinates dataframe")
    for x, y in zip(coordinates["x"], coordinates["y"]):
        log.debug("x: %s | y: %s", f"{x:<6}", f"{y:<6}")
        document.getObject("Sketch").addGeometry(
            Part.Point(App.Vector(float(x), float(y), 0))
        )
        document.recompute()

    # Check how many x coordinates there are in the dataframe
    number_of_coord = coordinates["x"].count()
    log.debug("Number of coordinates: %s", number_of_coord)
    # Draw a B-spline by knots through the points

    # Define the missing variables
    _finalbsp_poles = []
    _finalbsp_mults = []
    _finalbsp_knots = []

    log.debug("Drawing a B-spline by knots through the points")
    import Sketcher  # Import the Sketcher module

    document.getObject("Sketch").addGeometry(
        Part.BSplineCurve(
            _finalbsp_poles, _finalbsp_mults, _finalbsp_knots, False, 3, None, False
        ),
        False,
    )
    conList = []
    for i in range(0, number_of_coord):
        log.debug("Appending B-Spline Knot Point: %s/%s", i + 1, number_of_coord)
        conList.append(
            Sketcher.Constraint(
                "InternalAlignment:Sketcher::BSplineKnotPoint",
                number_of_coord + i,
                1,
                number_of_coord * 2,
                i,
            )
        )

    # Save the new document
    document.saveAs(f"{cwd}/cad/{name}.FCStd")
    log.debug("Document saved as %s.FCStd", name)


# Get the current working directory
cwd = os.getcwd()

for file in os.listdir(cwd + "/profiles"):
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
        # log.debug(df)

        # Remove .txt from the filename
        log.debug("Removing .txt from the filename")
        filename = file[:-4]
        log.debug("Filename: %s", filename)

        # Save the file as a csv
        log.debug("Saving the file as a csv")
        df.to_csv(f"profiles/{filename}.csv", index=False, header=False)
        log.info("Saved %s as a csv", filename)

        # Draw the profile from the csv
        log.info("Drawing the profile from coordinates provided in %s.csv", filename)
        draw_from_csv_coordinates(filename, df)
