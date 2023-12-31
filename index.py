import os
import sys
import pandas as pd

# Setup the FreeCAD import
# It's possible to do both on Windows and Linux
# But it's easier to do it on Linux
# Docs: https://wiki.freecad.org/Embedding_FreeCAD
freecad_path = "/usr/lib/freecad-python3/lib"
sys.path.append(freecad_path)
import FreeCAD  # Import FreeCAD after adding the path


# Function to draw the profile from the csv
def draw_from_csv_coordinates(coordinates, **kwargs):
    # To activate Part Design workbench:
    # Gui.activateWorkbench("PartDesignWorkbench")

    # To create a new document
    # App.newDocument()

    # Rename the newly created document
    # FreeCAD.getDocument('Unnamed').Label = <new_file_name>

    # Add a new body to the document
    # App.activeDocument().addObject('PartDesign::Body','Body')

    # Rename the body
    # App.getDocument('Unnamed').getObject('Body').Label = <new_body_name>
    # App.getDocument('Unnamed').recompute()

    # For the Body add a sketch in teh YZ plane
    # App.getDocument('Unnamed').getObject('Body').newObject('Sketcher::SketchObject','Sketch')
    # App.getDocument('Unnamed').getObject('Sketch').Support = (App.getDocument('Unnamed').getObject('YZ_Plane'),[''])
    # App.getDocument('Unnamed').getObject('Sketch').MapMode = 'FlatFace'
    # App.getDocument('Unnamed').recompute()
    # import PartDesignGui

    # Create Points for each coordinate
    # App.getDocument('Unnamed').getObject('Sketch').addGeometry(Part.Point(App.Vector(x,y,0)))
    # RECOMPUTE AFTER YOU CREATE A POINT: App.getDocument('Unnamed').recompute()
    #
    return


# Get the current working directory
cwd = os.getcwd()

for file in os.listdir(cwd + "/profiles"):
    if file.endswith(".txt"):
        print(file)
        # Open the file
        df = pd.read_csv("profiles/" + file)

        # Remove .txt from the filename
        filename = file[:-4]

        # Save the file as a csv
        df.to_csv(f"profiles/{filename}.csv", index=False, header=False)

        # Draw the profile from the csv
        draw_from_csv_coordinates(df)
