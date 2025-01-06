import numpy as np
import time
from PIL import Image

# north = downward
# east = rightward

# NOTE: change the following paths to the paths where your player coordinates are stored.
# minecraft
# overworld_path = r"C:\Users\yuane\AppData\Roaming\.minecraft\minecraft_overworld_player_coordinates.txt"
# nether_path = r"C:\Users\yuane\AppData\Roaming\.minecraft\minecraft_the_nether_player_coordinates.txt"
# end_path = r"C:\Users\yuane\AppData\Roaming\.minecraft\minecraft_the_end_player_coordinates.txt"

# dev
overworld_path = r"C:\Users\yuane\Documents\cmap-origin\cmap-forge-1.21-51.0.33\run\minecraft_overworld_player_coordinates.txt"
nether_path = r"C:\Users\yuane\Documents\cmap-origin\cmap-forge-1.21-51.0.33\run\minecraft_the_nether_player_coordinates.txt"
end_path = r"C:\Users\yuane\Documents\cmap-origin\cmap-forge-1.21-51.0.33\run\minecraft_the_end_player_coordinates.txt"

resolution = 32768

def generate_image(file_name, coordinates, resolution):
    """
    generate an image with the given coordinates and resolution.
    """
    # create a white image
    image = np.ones((resolution, resolution, 3), dtype=np.uint8) * 255
    # start from the center of the image
    offset = resolution // 2
    # mark the coordinates with black pixels
    image[coordinates[:, 0] + offset, coordinates[:, 1] + offset] = [0, 0, 0]

    image = Image.fromarray(image)
    image.save(f"{file_name}.png")

def get_coordinates(file_path):
    """
    read from the file and return the coordinates as a numpy array; [(x, z), ...]
    """
    coordinates = [(0, 0)]
    with open(file_path, "r") as file:
        if file.readline() == "": return np.array(coordinates)
        for line in file:
            x, z = map(float, line.strip().split(", "))
            coordinates.append((round(x), round(z)))
    return np.array(coordinates)

start_time = time.time()

overworld_coordinates = get_coordinates(overworld_path)
generate_image("overworld", overworld_coordinates, resolution)
overworld_coordinates = None

# uncomment the following lines to generate images for the nether and the end coordinates.
# nether_coordinates = get_coordinates(nether_path)
# generate_image("nether", nether_coordinates, resolution)
# nether_coordinates = None

# end_coordinates = get_coordinates(end_path)
# generate_image("end", end_coordinates, resolution)
# end_coordinates = None

end_time = time.time()
print("Time taken: {:.2f} seconds".format(end_time - start_time))