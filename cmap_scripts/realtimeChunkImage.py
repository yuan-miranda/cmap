# NOTE: This runs in the server.

import numpy as np
import time
from PIL import Image
import sys
import os
import psycopg2

# north = downward
# east = rightward

# for the cmap plugin
# /cmap dbconfig <host> <port> <dbname> <user> <password>

DB_HOST = ""
DB_PORT = 5432
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = ""

MAX_CHUNK_SIZE = 8192
overworld_path = "minecraft_overworld_player_coordinates.txt"
nether_path = "minecraft_the_nether_player_coordinates.txt"
end_path = "minecraft_the_end_player_coordinates.txt"

overworld_path_cumulative = "minecraft_overworld_player_coordinates_cumulative.txt"
nether_path_cumulative = "minecraft_the_nether_player_coordinates_cumulative.txt"
end_path_cumulative = "minecraft_the_end_player_coordinates_cumulative.txt"

def generate_image(resolution, type="overworld", zoom_levels=1):
    """
    generates blank white images. Each zoom_level the quality of the image doesnt increase, the number of tiles does. It will be kind of pixelated.
    """
    os.makedirs(f"../tiles/{type}", exist_ok=True)

    if resolution > MAX_CHUNK_SIZE and (resolution & (resolution - 1)) != 0:
        print(f"resolution must be divisible by 8192, and is even i.e. 8192=1x1, 16384=2x2")
        return

    chunk_multiplier = max(1, resolution // MAX_CHUNK_SIZE)

    for zoom_level in range(zoom_levels):
        base_chunk_size = resolution // (2 ** zoom_level)
        adjusted_chunk_size = base_chunk_size // chunk_multiplier
        chunk_per_axis = resolution // base_chunk_size
        total_chunks = chunk_per_axis * chunk_multiplier

        for x_level in range(total_chunks):
            for y_level in range(total_chunks):
                chunk_image = Image.fromarray(np.ones((adjusted_chunk_size, adjusted_chunk_size), dtype=np.uint8) * 255, mode="L")
                tile = f"../tiles/{type}/{zoom_level}/{x_level}/{y_level}.png"

                os.makedirs(os.path.dirname(tile), exist_ok=True)
                chunk_image.save(tile)

def update_image(resolution, coordinates, type="overworld"):
    """
    updates the image with the coordinates. The coordinates are black pixels on the image.
    """
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

    os.makedirs(f"../tiles/{type}", exist_ok=True)

    # early return if the coordinates is empty
    if len(coordinates) == 0: return

    # check if the resolution is valid
    if resolution > MAX_CHUNK_SIZE and (resolution & (resolution - 1)) != 0:
        print(f"resolution must be divisible by 8192, and is even i.e. 8192=1x1, 16384=2x2")
        return

    offset = resolution // 2

    # get zoom level folder names (0, 1, ...)
    zoom_levels = sorted(os.listdir(f"../tiles/{type}"), key=int)
    if not zoom_levels: return

    temp_tile = None
    temp_chunk_image = None

    try:
        chunk_multiplier = max(1, resolution // MAX_CHUNK_SIZE)

        for zoom_level in zoom_levels:
            zoom_level = int(zoom_level)
            base_chunk_size = resolution // (2 ** zoom_level)
            adjusted_chunk_size = base_chunk_size // chunk_multiplier
            chunk_per_axis = resolution // base_chunk_size
            total_chunks = chunk_per_axis * chunk_multiplier

            for x_level in range(total_chunks):
                for y_level in range(total_chunks):
                    tile = f"../tiles/{type}/{zoom_level}/{x_level}/{y_level}.png"
                    chunk_image = Image.open(tile)

                    temp_tile = tile
                    temp_chunk_image = chunk_image.copy()
                    for x, z in coordinates:
                        row = (x + offset) // adjusted_chunk_size
                        col = (z + offset) // adjusted_chunk_size

                        if x_level == row and y_level == col:
                            start_x = row * adjusted_chunk_size - offset
                            start_z = col * adjusted_chunk_size - offset
                            x_rel = x - start_x
                            z_rel = z - start_z

                            # check if the pixel is within the chunk
                            if 0 <= x_rel < adjusted_chunk_size and 0 <= z_rel < adjusted_chunk_size:
                                chunk_image.putpixel((x_rel, z_rel), 0)

                    chunk_image.save(tile)

    except Exception as e:
        if temp_chunk_image is not None:
            temp_chunk_image.save(temp_tile)
        raise e

def get_db_connection():
    """
    connect to the database and return the connection
    """
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def get_coordinates_from_db(file_path, table_name):
    """
    read from the database and return the coordinates as a numpy array; [(x, z), ...]
    """
    coordinates = []
    cumulative_path = file_path.replace("player_coordinates", "player_coordinates_cumulative")
    conn = get_db_connection()
    if not conn: return np.array(coordinates)

    try:
        with conn.cursor() as cursor, open(cumulative_path, "a") as cumulative_file:
            query = f"SELECT x, z FROM {table_name}"
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                x, z = row
                cumulative_file.write(f"{x}, {z}\n")
                coordinates.append((round(x), round(z)))
            
            cumulative_file.flush()
    except Exception as e:
        print(f"Error getting coordinates from the database: {e}")
    finally:
        conn.close()

    return np.array(coordinates)


def get_coordinates_from_db_and_truncate(file_path, table_name):
    """
    read from the database and return the coordinates as a numpy array; [(x, z), ...]. Truncate the table after reading.
    """
    coordinates = []
    cumulative_path = file_path.replace("player_coordinates", "player_coordinates_cumulative")
    conn = get_db_connection()
    if not conn: return np.array(coordinates)

    try:
        with conn.cursor() as cursor, open(cumulative_path, "a") as cumulative_file:
        # with conn.cursor() as cursor:
            query = f"SELECT x, z FROM {table_name}"
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                x, z = row
                cumulative_file.write(f"{x}, {z}\n")
                coordinates.append((round(x), round(z)))

            cumulative_file.flush()

            # truncate the table
            query = f"TRUNCATE TABLE {table_name}"
            cursor.execute(query)
            conn.commit()
    except Exception as e:
        print(f"Error getting coordinates from the database: {e}")
    finally:
        conn.close()

    return np.array(coordinates)

def get_coordinates(file_path):
    """
    read from the file and return the coordinates as a numpy array; [(x, z), ...]
    """
    coordinates = []
    cumulative_path = file_path.replace("player_coordinates", "player_coordinates_cumulative")
    with open(file_path, "r") as file, open(cumulative_path, "a") as cumulative_file:
        if file.readline() == "": return np.array(coordinates)
        for line in file:
            try:
                x, z = map(float, line.strip().split(", "))
                cumulative_file.write(f"{x}, {z}\n")
                coordinates.append((round(x), round(z)))
            except Exception as e:
                continue

        cumulative_file.flush()
        file.close()
    return np.array(coordinates)

def get_coordinates_and_truncate(file_path):
    """
    read from the file and return the coordinates as a numpy array; [(x, z), ...]. Truncate the file after reading.
    """
    coordinates = []
    cumulative_path = file_path.replace("player_coordinates", "player_coordinates_cumulative")
    with open(file_path, "r+") as file, open(cumulative_path, "a") as cumulative_file:
        lines = file.readlines()
        if lines == []: return np.array(coordinates)
        for line in lines:
            try:
                x, z = map(float, line.strip().split(", "))
                cumulative_file.write(f"{x}, {z}\n")
                coordinates.append((round(x), round(z)))
            except Exception as e:
                continue
        
        cumulative_file.flush()
        # truncate the file
        file.seek(0)
        file.truncate(0)
        file.close()
    return np.array(coordinates)

def main():
    resolution = 8192 * 4
    if len(sys.argv) > 1 and sys.argv[1] in ["update", "init", "realtime"]:
        # validate the arguments
        action = sys.argv[1]

        # update the images in real time
        if action == "realtime":
            if len(sys.argv) > 2:
                print("usage: python realtimeChunkImage.py realtime\n")
                return
            try:
                while True:
                    start_time_get_coordinates = time.time()
                    overworld_coordinates = get_coordinates_from_db_and_truncate(overworld_path, "overworld")
                    nether_coordinates = get_coordinates_from_db_and_truncate(nether_path, "nether")
                    end_coordinates = get_coordinates_from_db_and_truncate(end_path, "the_end")
                    end_time_get_coordinates = time.time()

                    type_coordinates = {
                        "overworld": overworld_coordinates,
                        "nether": nether_coordinates,
                        "end": end_coordinates
                    }

                    # update each type
                    start_time_update_image = time.time()
                    for type in type_coordinates:
                        coordinates = type_coordinates.get(type, overworld_coordinates)
                        update_image(resolution, coordinates, type)
                    end_time_update_image = time.time()

                    print(f"o: {len(overworld_coordinates)} n: {len(nether_coordinates)} e: {len(end_coordinates)} get coordinates: {end_time_get_coordinates - start_time_get_coordinates:.2f} seconds update image: {end_time_update_image - start_time_update_image:.2f} seconds")

                    time.sleep(1)
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                return

        type = sys.argv[2] if len(sys.argv) > 2 else "overworld"
        zoom_level = int(sys.argv[3]) if len(sys.argv) > 3 else 1

        # "update" will use the coordinates from the file instead of the database.
        type_coordinates = {
            "overworld": get_coordinates(overworld_path),
            "nether": get_coordinates(nether_path),
            "end": get_coordinates(end_path)
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
        print("usage: python realtimeChunkImage.py init [<type=OVERWORLD|nether|end> <zoom_level=1>]")
        print("usage: python realtimeChunkImage.py update [<type=OVERWORLD|nether|end>]\n")
        print("usage: python realtimeChunkImage.py realtime\n")
        print("\tinit: generate blank images")
        print("\tupdate: update the existing images")
        print("\trealtime: update the existing images in real time. ctrl+c to stop the program")
        print("\ttype: specify the type of minecraft world dimension (overworld, nether, end) default is 'overworld'")
        print("\tzoom_level: specify the how many times the image should be divided into chunks, used in Leaflet.js, default is 1\n")

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("total time taken: {:.2f} seconds".format(end_time - start_time))
