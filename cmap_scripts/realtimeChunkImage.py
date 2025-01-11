# NOTE: This runs in the server.

import numpy as np
import time
from PIL import Image
import sys
import os

# north = downward
# east = rightward

overworld_path = "minecraft_overworld_player_coordinates.txt"
nether_path = "minecraft_the_nether_player_coordinates.txt"
end_path = "minecraft_the_end_player_coordinates.txt"

def generate_image(resolution, type="overworld", zoom_levels=1):
    """
    generates blank white images. Each zoom_level the quality of the image doesnt increase, the number of tiles does. It will be kind of pixelated.
    """
    os.makedirs(f"../tiles/{type}", exist_ok=True)

    for zoom_level in range(zoom_levels):
        chunk_size = resolution // (2 ** zoom_level)
        num_chunks = resolution // chunk_size

        for x_level in range(num_chunks):
            for y_level in range(num_chunks):
                chunk_image = Image.fromarray(np.ones((chunk_size, chunk_size, 3), dtype=np.uint8) * 255)
                tile = f"../tiles/{type}/{zoom_level}/{x_level}/{y_level}.png"

                os.makedirs(os.path.dirname(tile), exist_ok=True)
                chunk_image.save(tile)

def update_image(resolution, coordinates, type="overworld"):
    # structure of the tiles folder:
    # tiles/type/zoom_level/x/y.png
    # 0/
    #   overworld/
    #     0/
    #       0/
    #         0.png
    #         1.png
    #         ...
    #       1/
    #         ...
    #       .../
    #     1/
    #     .../
    #   nether/
    #     ...
    #   end/
    #     ...
    # .../

    # tiles/type/zoom_level/x/y.png
    # same structure as tiles

    # early return if the coordinates is empty
    if len(coordinates) == 0: return

    os.makedirs(f"../tiles/{type}", exist_ok=True)
    offset = resolution // 2

    # get zoom level folder names (0, 1, ...)
    zoom_levels = sorted(os.listdir(f"../tiles/{type}"), key=int)
    if not zoom_levels: return

    temp_tile = None
    temp_chunk_image = None
    try:
        for zoom_level in zoom_levels:
            chunk_size = resolution // (2 ** int(zoom_level))
            num_chunks = resolution // chunk_size

            for x_level in range(num_chunks):
                for y_level in range(num_chunks):
                    tile = f"../tiles/{type}/{zoom_level}/{x_level}/{y_level}.png"
                    chunk_image = Image.open(tile)

                    temp_tile = tile
                    temp_chunk_image = chunk_image.copy()
                    for x, z in coordinates:
                        row = (x + offset) // chunk_size
                        col = (z + offset) // chunk_size

                        if x_level == row and y_level == col:
                            start_x = row * chunk_size - offset
                            start_z = col * chunk_size - offset
                            x_rel = x - start_x
                            z_rel = z - start_z

                            # check if the pixel is within the chunk
                            if 0 <= x_rel < chunk_size and 0 <= z_rel < chunk_size:
                                chunk_image.putpixel((x_rel, z_rel), (0, 0, 0))

                    chunk_image.save(tile)

    except Exception as e:
        if temp_chunk_image is not None:
            temp_chunk_image.save(temp_tile)
        raise e
    
    return

def get_coordinates(file_path):
    """
    read from the file and return the coordinates as a numpy array; [(x, z), ...]
    """
    coordinates = []
    with open(file_path, "r") as file:
        if file.readline() == "": return np.array(coordinates)
        for line in file:
            try:
                x, z = map(float, line.strip().split(", "))
                coordinates.append((round(x), round(z)))
            except Exception as e:
                continue
        file.close()
    return np.array(coordinates)

def get_coordinates_and_truncate(file_path):
    """
    read from the file and return the coordinates as a numpy array; [(x, z), ...]
    """
    coordinates = []
    with open(file_path, "r+") as file:
        lines = file.readlines()
        if lines == []: return np.array(coordinates)
        for line in lines:
            try:
                x, z = map(float, line.strip().split(", "))
                coordinates.append((round(x), round(z)))
            except Exception as e:
                continue
        
        # truncate the file
        file.seek(0)
        file.truncate(0)
        file.close()
    return np.array(coordinates)

def main():
    resolution = 8192
    overworld_coordinates = get_coordinates(overworld_path)
    nether_coordinates = get_coordinates(nether_path)
    end_coordinates = get_coordinates(end_path)

    if len(sys.argv) > 1 and sys.argv[1] in ["update", "init", "realtime"]:
        # validate the arguments
        action = sys.argv[1]

        # update the images in real time
        if action == "realtime":
            if len(sys.argv) > 2:
                print("usage: python chunkImage.py realtime\n")
                return
            try:
                while True:
                    overworld_coordinates = get_coordinates_and_truncate(overworld_path)
                    nether_coordinates = get_coordinates_and_truncate(nether_path)
                    end_coordinates = get_coordinates_and_truncate(end_path)

                    type_coordinates = {
                        "overworld": overworld_coordinates,
                        "nether": nether_coordinates,
                        "end": end_coordinates
                    }

                    # update each type
                    for type in type_coordinates:
                        coordinates = type_coordinates.get(type, overworld_coordinates)
                        update_image(resolution, coordinates, type)

                    time.sleep(5)

            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                return

        # if its not realtime
        type = sys.argv[2] if len(sys.argv) > 2 else "overworld"
        zoom_level = int(sys.argv[3]) if len(sys.argv) > 3 else 1

        type_coordinates = {
            "overworld": overworld_coordinates,
            "nether": nether_coordinates,
            "end": end_coordinates
        }

        # check if the type is valid
        if type not in type_coordinates:
            print(f"invalid type: {type}\n")
            print(f"\ttype: {', '.join(type_coordinates.keys())}\n")
            return

        # update the images
        if action == "update":
            coordinates = type_coordinates.get(type, overworld_coordinates)
            update_image(resolution, coordinates, type)

        # generate blank images
        elif action == "init":
            if zoom_level is not None:
                generate_image(resolution, type, zoom_level)
            else:
                generate_image(resolution, type)
        else:
            print("invalid action")
    else:
        print("usage: python chunkImage.py init [<type=OVERWORLD|nether|end> <zoom_level=1>]")
        print("usage: python chunkImage.py update [<type=OVERWORLD|nether|end>]\n")
        print("usage: python chunkImage.py realtime\n")
        print("\tinit: generate blank images")
        print("\tupdate: update the existing images")
        print("\trealtime: update the existing images in real time. ctrl+c to stop the program")
        print("\ttype: specify the type of minecraft world dimension (overworld, nether, end) default is 'overworld'")
        print("\tzoom_level: specify the how many times the image should be divided into chunks, used in Leaflet.js, default is 1\n")

        # there is no option to update the zoom level of the existing images becasue that would mean the images would have to be resized and the coordinates would have to be recalculated, too lazy lol.

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("total time taken: {:.2f} seconds".format(end_time - start_time))
