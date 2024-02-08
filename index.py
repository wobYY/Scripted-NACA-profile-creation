import os
import sys
import pandas as pd
import logging
from utils.logging import CustomLogger  # pylint-disable: C0411

# Setup the logger
# usually you use __name__ here instead of "snpc"
# but because this is a script, not a module, __name__ is __main__
log = CustomLogger().get_logger("snpc", level="DEBUG")

# Setup the FreeCAD import
# It's possible to do both on Windows and Linux
# But it's easier to do it on Linux
# Docs: https://wiki.freecad.org/Embedding_FreeCAD
sys.path.append("/usr/lib/freecad-python3/lib/")

# Because PartDesign is not imported by default with the imports above
# We need to import the module folder for PartDesign
# Forum: https://forum.freecad.org/viewtopic.php?style=4&p=677043#p677043
sys.path.append("/usr/lib/freecad/Mod")

# pylint-disable: E0401
import FreeCAD  # Import FreeCAD after adding the path
from FreeCAD import Base

import PartDesign  # Import PartDesign after adding the Mod path
import Sketcher  # Import Sketcher after adding the Mod path


def __coincident(sketch, f_line_id, f_edge_id, s_line_id, s_edge_id):
    """This function constrains two lines

    Args:
        sketch (object): Sketch object
        f_line_id (int): First line ID
        f_edge_id (int): First edge ID
        s_line_id (int): Second line ID
        s_edge_id (int): Second edge ID
    """
    sketch.addConstraint(
        Sketcher.Constraint("Coincident", f_line_id, f_edge_id, s_line_id, s_edge_id)
    )


def __ll_id(sketch):
    """This function returns the last line ID of the sketch

    Args:
        sketch (object): Sketch object

    Returns:
        int: Last line ID
    """
    return int(len(sketch.Geometry) - 1)


# Function to draw the profile from the csv
def draw_from_csv_coordinates(name, coordinates, **kwargs):
    # Make sure that the "coordinates" variable is a dataframe
    if not isinstance(coordinates, pd.DataFrame):
        logging.error("The coordinates variable is not a dataframe")
        raise TypeError("The coordinates variable is not a dataframe")

    # Check if the dataframe has the correct columns
    if not "x" in coordinates.columns or not "y" in coordinates.columns:
        logging.error("The dataframe doesn't have the correct columns")
        raise ValueError("The dataframe doesn't have the correct columns")

    # Check the type of values in the dataframe and convert them to floats
    logging.debug("Checking the type of values in the dataframe")
    if coordinates["x"].dtype != float:
        logging.debug("Converting the x values to floats")
        coordinates["x"] = coordinates["x"].astype(float)
    if coordinates["y"].dtype != float:
        logging.debug("Converting the y values to floats")
        coordinates["y"] = coordinates["y"].astype(float)

    # Ask the user if they want to scale the profile
    # If they do, ask them for the scale factor
    # If they don't, set the scale factor to 1
    logging.debug("Checking if the user wants to scale the profile")
    scale_factor = 1 if not "scale_factor" in kwargs else kwargs.get("scale_factor")
    if (
        input(f"Do you want to scale the {name} profile? (y/n): ").lower() == "y"
        and kwargs.get("scale_factor") is None
    ):
        logging.debug("User wants to scale the profile")
        scale_factor = float(input("Enter the scale factor: "))
        logging.debug("Scale factor set to: %s", scale_factor)
        coordinates["x"] = coordinates["x"] * scale_factor
        coordinates["y"] = coordinates["y"] * scale_factor
        logging.debug("Profile scaled")

    # Check if "cad" folder exists, if it doesn't create it
    logging.debug("Checking if cad folder exists")
    if not os.path.exists(f"{cwd}/cad"):
        logging.debug("cad folder doesn't exist, creating it")
        os.mkdir(f"{cwd}/cad")
        logging.debug("cad folder created")

    # Create a new document
    logging.debug("Creating a new document")
    document = App.newDocument()
    logging.debug("Document created, preparing to save as %s.FCStd", name)
    # If the document already exists, delete the existing document
    if os.path.exists(f"{cwd}/cad/{name}.FCStd"):
        logging.debug("Document already exists, deleting the existing document")
        os.remove(f"{cwd}/cad/{name}.FCStd")
        logging.debug("Existing document deleted")

    # Add a new body to the document
    logging.debug("Adding a new body to the document")
    logging.debug("Ensuring the body name is valid")
    body_name = name.replace(" ", "_").replace("-", "_").lower()
    logging.debug("Setting the body name to: %s", body_name)
    body = document.addObject("PartDesign::Body", body_name)
    body.Visibility = 1
    document.recompute()
    logging.debug("Body added to the document")

    # For the Body add a sketch in teh YZ plane
    sketch = body.newObject("Sketcher::SketchObject", "Sketch")
    sketch.Support = (
        document.getObject("YZ_Plane"),
        [""],
    )
    sketch.MapMode = "FlatFace"
    document.recompute()

    # Check how many x coordinates there are in the dataframe
    number_of_coord = coordinates["x"].count()
    logging.debug("Number of coordinates: %s", number_of_coord)

    # Create Points for each coordinate
    # for x, y in coordinates in the "coordinates" dataframe
    logging.debug("Checking the coordinates dataframe")
    V = Base.Vector
    poles = []  # Poles for the B-spline
    for x, y in zip(coordinates["x"], coordinates["y"]):
        logging.debug(
            "Processing point with coords: x: %s | y: %s", f"{x:<6}", f"{y:<6}"
        )
        sketch.addGeometry(Part.Point(App.Vector(float(x), float(y), 0)))
        document.recompute()

        # In order to have a valid sketch in FreeCAD
        # We need to constraint all of our geometries in the sketch
        # After which we'll be able to extrude the sketch into a solid
        # Docs: https://wiki.freecad.org/Sketcher_scripting
        logging.debug("Constraining the %s", sketch.Geometry[-1])
        sketch.addConstraint(
            Sketcher.Constraint(
                "DistanceX", -2, 1, __ll_id(sketch), 1, App.Units.Quantity(f"{x} mm")
            )
        )
        document.recompute()

        sketch.addConstraint(
            Sketcher.Constraint(
                "DistanceY", __ll_id(sketch), 1, -1, 1, App.Units.Quantity(f"{y} mm")
            )
        )
        document.recompute()
        logging.debug("Points constrained")

        # After each point is created, we need to recompute the document
        logging.debug("Recomputing the document")
        document.recompute()

        logging.debug("Point created and constrained")
        poles.append(V(float(x), float(y)))
        logging.debug(
            "Point added to the list of poles for the B-Spline creation later on"
        )

    # Draw a B-spline by knots through the points
    # Docs: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/BSplineCurve_API.md
    logging.debug("Drawing B-Spline")
    b_spline = Part.BSplineCurve()
    b_spline.buildFromPoles(poles)
    sketch.addGeometry(b_spline)
    document.recompute()
    logging.debug("B-Spline drawn")

    # Connect the first and last point with a straight line
    logging.debug("Connecting the first and last point with a straight line")
    closing_line = Part.LineSegment(poles[0], poles[-1])
    sketch.addGeometry(closing_line)
    document.recompute()

    # Add constraints for the line
    __coincident(sketch, __ll_id(sketch), 1, 0, 1)
    __coincident(sketch, __ll_id(sketch), 2, number_of_coord - 1, 1)
    document.recompute()
    logging.debug("Profile closed with a straight line")

    # Creating the domain around the profile
    logging.info("Profile created, creating the domain around the profile")

    # Get the minimum and maximum x and y coordinates
    logging.debug("Getting the minimum and maximum x and y coordinates")
    min_x = coordinates["x"].min()
    max_x = coordinates["x"].max()
    min_y = coordinates["y"].min()
    max_y = coordinates["y"].max()
    logging.debug("Minimum x: %s | Maximum x: %s", f"{min_x:<6}", f"{max_x:<6}")
    logging.debug("Minimum y: %s | Maximum y: %s", f"{min_y:<6}", f"{max_y:<6}")

    # Calculating the length of the profile
    logging.debug("Calculating the length of the profile")
    length = max_x - min_x

    # Calculating the dimensions for the domain
    logging.debug("Calculating the dimensions for the domain")
    x_front = min_x - (length * 3)  # 3x the profile length for the flow to develop
    x_back = max_x + (length * 7)  # 7x the profile length
    y_above = max_y + (length * 3)  # 3x the profile length
    y_below = min_y - (length * 3)  # 3x the profile length

    # Draw the domain
    # According to the Constraint documentation
    # Docs: https://wiki.freecad.org/Sketcher_scripting
    # To constrain these lines you need to use
    # ...er.Constraint("Coincient", first_line_id, edge_id, second_line_id, edge_id)
    # Where edge ID is 0 for starting edge, 1 for ending and 2 for middle of the line
    logging.info("Drawing the domain")
    # Drawing the top line
    logging.debug("Drawing the top line of the domain")
    sketch.addGeometry(Part.LineSegment(V(x_front, y_above, 0), V(x_back, y_above, 0)))

    # Constrain the line to be horizontal
    logging.debug("Constraining line: %s", sketch.Geometry[-1])
    sketch.addConstraint(Sketcher.Constraint("Horizontal", __ll_id(sketch)))

    # Adding distances from origin to the line
    sketch.addConstraint(
        Sketcher.Constraint(
            "DistanceX", -1, 1, __ll_id(sketch), 1, App.Units.Quantity(f"{x_front} mm")
        )
    )
    sketch.addConstraint(
        Sketcher.Constraint(
            "DistanceX", -1, 1, __ll_id(sketch), 2, App.Units.Quantity(f"{x_back} mm")
        )
    )
    sketch.addConstraint(
        Sketcher.Constraint(
            "DistanceY", __ll_id(sketch), 1, -1, 1, App.Units.Quantity(f"{y_above} mm")
        )
    )

    # Drawing the right line
    logging.debug("Drawing the right line of the domain")
    sketch.addGeometry(Part.LineSegment(V(x_back, y_above, 0), V(x_back, y_below, 0)))

    # Constrain the line to be vertical
    logging.debug("Constraining line: %s", sketch.Geometry[-1])
    sketch.addConstraint(Sketcher.Constraint("Vertical", __ll_id(sketch)))

    # Constrain the last edge of 1st line with the first edge of the 2nd line
    __coincident(sketch, __ll_id(sketch) - 1, 2, __ll_id(sketch), 1)

    # Drawing the bottom line
    logging.debug("Drawing the bottom line of the domain")
    sketch.addGeometry(Part.LineSegment(V(x_back, y_below, 0), V(x_front, y_below, 0)))

    # Constrain the line to be horizontal
    logging.debug("Constraining line: %s", sketch.Geometry[-1])
    sketch.addConstraint(Sketcher.Constraint("Horizontal", __ll_id(sketch)))

    # Adding distances from origin to the line
    sketch.addConstraint(
        Sketcher.Constraint(
            "DistanceY", __ll_id(sketch), 1, -1, 1, App.Units.Quantity(f"{y_below} mm")
        )
    )

    # Constrain the last edge of 2nd line with the first edge of the 3rd line
    __coincident(sketch, __ll_id(sketch) - 1, 2, __ll_id(sketch), 1)

    # Drawing the left line
    logging.debug("Drawing the left line of the domain")
    sketch.addGeometry(Part.LineSegment(V(x_front, y_below, 0), V(x_front, y_above, 0)))

    # Constrain the line to be vertical
    logging.debug("Constraining line: %s", sketch.Geometry[-1])
    sketch.addConstraint(Sketcher.Constraint("Vertical", __ll_id(sketch)))

    # Constrain the last edge of the 3rd line with the first edge of the 4th line
    __coincident(sketch, __ll_id(sketch) - 1, 2, __ll_id(sketch), 1)

    # Constrain the last edge of the 4th line with the first edge of the 1st line
    __coincident(sketch, __ll_id(sketch) - 3, 1, __ll_id(sketch), 2)
    document.recompute()
    logging.info("Domain created, profile ready to be extruded")

    # Extrude the sketch
    logging.info("Extruding the sketch")
    pad_name = f"{name.lower()}_extrude"
    body.newObject("PartDesign::Pad", pad_name).Profile = (
        sketch  # Base sketch is sketch
    )
    document.getObject(pad_name).Length = kwargs.get(
        "extrude_length", 100
    )  # Extrude length is 100mm by default if not specified in kwargs
    document.recompute()
    # document.getObject(pad_name).AlongSketchNormal = 1  # Normal to the sketch
    # document.getObject(pad_name).TaperAngle = 0  # No taper angle
    document.getObject(pad_name).UseCustomVector = False  # Don't use custom vector
    document.getObject(pad_name).Midplane = 1  # Don't use midplane
    document.getObject(pad_name).Direction = (1, -0, 0)
    document.getObject(pad_name).Type = 0
    document.getObject(pad_name).UpToFace = None
    document.getObject(pad_name).Reversed = 0
    document.getObject(pad_name).Offset = 0
    document.getObject(pad_name).Visibility = 1  # Show the extrusion
    sketch.Visibility = 0  # Hide the sketch
    document.recompute()
    logging.info("Sketch extruded by %s mm", kwargs.get("extrude_length", 100))

    # Save the new document
    # ### Begin command Std_Export
    # __objs__ = []
    # __objs__.append(FreeCAD.getDocument("SAMPLE_NACA_FILE").getObject("sample_naca_file_extrude"))
    # import ImportGui
    # if hasattr(ImportGui, "exportOptions"):
    #     options = ImportGui.exportOptions(u"C:/Users/wobY/Downloads/temp/SAMPLE_NACA_FILE.step")
    #     ImportGui.export(__objs__, u"C:/Users/wobY/Downloads/temp/SAMPLE_NACA_FILE.step", options)
    # else:
    #     ImportGui.export(__objs__, u"C:/Users/wobY/Downloads/temp/SAMPLE_NACA_FILE.step")
    #
    # del __objs__
    # ### End command Std_Export
    document.saveAs(f"{cwd}/cad/{name}.FCStd")
    logging.debug("Document saved as %s.FCStd", name)


# Get the current working directory
cwd = os.getcwd()


def process_all_profiles_in_parent_dir():
    logging.info("Checking for all text files in the /profiles folder")
    for file in os.listdir(cwd + "/profiles"):
        if file.endswith(".txt"):
            logging.debug("Found a .txt file (%s), converting to .csv", file)

            # Open the file
            with open("profiles/" + file, "r") as f:
                lines = f.readlines()

            # If the file contains NACA in the first line remove the first line
            logging.debug("Checking if the first line contains NACA")
            if "NACA" in lines[0]:
                logging.debug("First line contains NACA, removing the first line")
                lines = lines[1:]

            # Read the file as a dataframe
            logging.debug("Storing the file as a dataframe")
            df = pd.DataFrame([line.split() for line in lines], columns=["x", "y"])

            # Remove .txt from the filename
            logging.debug("Removing .txt from the filename")
            filename = file[:-4]
            logging.debug("Filename: %s", filename)

            # Save the file as a csv
            logging.debug("Saving the processed file as a csv")
            df.to_csv(f"profiles/{filename}.csv", index=False, header=False)
            logging.info("Saved %s as a csv", filename)

            # Draw the profile from the csv
            logging.info(
                "Drawing the profile from coordinates provided in %s.csv", filename
            )
            draw_from_csv_coordinates(filename, df)


if __name__ == "__main__":
    process_all_profiles_in_parent_dir()
