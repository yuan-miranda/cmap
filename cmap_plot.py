# OUTDATED

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# north = downward
# east = rightward

overworld_path = "minecraft_overworld_player_coordinates_cumulative.txt"
nether_path = "minecraft_the_nether_player_coordinates_cumulative.txt"
end_path = "minecraft_the_end_player_coordinates_cumulative.txt"

resolution = 100000

def get_coordinates(file_path):
    """
    read from the file and return the coordinates as a numpy array; [(x, z), ...]
    """
    # always mark the 0, 0 coordinate
    coordinates = [(0, 0)]

    # read the coordinates from the file
    with open(file_path, "r") as file:
        if file.readline() == "":
            return np.array(coordinates)
        for line in file:
            x, z = map(float, line.strip().split(", "))
            coordinates.append((x, z))
    return np.array(coordinates)

def init():
    scatter.set_offsets(np.empty((0, 2)))
    return scatter,

def update(frame):
    coordinates = get_coordinates(overworld_path)
    scatter.set_offsets(coordinates)
    return scatter,

def loop():
    while True:
        yield

# configuration for the plot:
fig, ax = plt.subplots()
ax.set_xlim(-resolution // 2, resolution // 2)
ax.set_ylim(-resolution // 2, resolution // 2)
ax.set_aspect("equal")
scatter = ax.scatter([], [], c="black", s=1)

# start and display the plot:
ani = animation.FuncAnimation(fig, update, frames=loop(), init_func=init, blit=False)
plt.show()