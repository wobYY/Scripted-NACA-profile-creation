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

    # For the Body add a sketch in the YZ plane
    log.debug("Adding a sketch in the YZ plane")
    document.getObject("Body").newObject("Sketcher::SketchObject", "Sketch")
    document.getObject("Sketch").Support = (
        document.getObject("YZ_Plane"),
        [""],
    )
    document.getObject("Sketch").MapMode = "FlatFace"
    document.recompute()
    log.debug("Sketch added in the YZ plane")

    # Get the x and y coordinates from the first row of the dataframe
    log.debug("Preparing to draw a B-Spline")
    num_of_coordinates = len(coordinates["x"])
    document.getObject("Sketch").addGeometry(
        Part.Circle(
            App.Vector(float(coordinates["x"][0]), float(coordinates["y"][0]), 0),
            App.Vector(0, 0, 1),
            10,
        ),
        True,
    )
    document.recompute()
    document.getObject("Sketch").addConstraint(
        Sketcher.Constraint("Weight", num_of_coordinates, 1.000000)
    )
    document.recompute()
    document.getObject("Sketch").addConstraint(
        Sketcher.Constraint("Coincident", float(num_of_coordinates), 3, i - 1, 1)
    )
    document.recompute()
    log.debug("Initial B-Spline prepared")

    # Need to run through a for loop for each point
    log.debug("Running a for loop for each point")
    for i in range(1, num_of_coordinates):
        log.debug("Setting up a B-Spline for point %s/%s", i, num_of_coordinates)
        document.getObject("Sketch").addGeometry(
            Part.Circle(
                App.Vector(float(coordinates["x"][i]), float(coordinates["y"][i]), 0),
                App.Vector(0, 0, 1),
                10,
            ),
            True,
        )
        document.recompute()
        document.getObject("Sketch").addConstraint(
            Sketcher.Constraint(
                "Equal",
                float(num_of_coordinates) - 1 + i,
                float(num_of_coordinates) + i,
            )
        )
        document.recompute()
        document.getObject("Sketch").addConstraint(
            Sketcher.Constraint(
                "Coincident", float(num_of_coordinates) + i, 3, float(i), 1
            )
        )
        document.recompute()
    log.debug("B-Spline set up for each point")

    # Create the list for the appVector
    log.debug("Creating the list for the appVector to draw the B-Spline")
    app_vector_list = []
    for x, y in zip(coordinates["x"], coordinates["y"]):
        app_vector_list.append(App.Vector(float(x), float(y)))
    document.getObject("Sketch").addGeometry(
        Part.BSplineCurve(
            app_vector_list,
            None,
            None,
            False,
            2,
            None,
            False,
        ),
        False,
    )
    log.debug("B-Spline drawn")

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
