import os
import pandas as pd

def draw_from_csv_coordinates(coordinates, **kwargs):
    
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