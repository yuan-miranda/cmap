import numpy as np
import time
from PIL import Image
import sys
import os
import psycopg2
import argparse

# north is down
# east is right

DB_HOST = ""
DB_PORT = 5432
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = ""

RESOLUTION = 32768
MAX_CHUNK_SIZE = 256

WORLD_NAME = "world"
OVERWORLD_PATH = f"worlds/{WORLD_NAME}/overworld.txt"
NETHER_PATH = f"worlds/{WORLD_NAME}/nether.txt"
END_PATH = f"worlds/{WORLD_NAME}/end.txt"

os.makedirs(f"worlds/{WORLD_NAME}", exist_ok=True)


def generate_image(dimension="overworld", zoom_levels=1):
    os.makedirs(f"tiles/{dimension}", exist_ok=True)

    base_chunks_per_axis = max(1, RESOLUTION // MAX_CHUNK_SIZE)
    for zoom_level in range(zoom_levels):
        zoomed_resolution = RESOLUTION // (2**zoom_level)
        chunks_per_axis = base_chunks_per_axis * (2**zoom_level)
        chunk_size = zoomed_resolution // chunks_per_axis

        for x_level in range(chunks_per_axis):
            for y_level in range(chunks_per_axis):
                chunk = Image.fromarray(
                    np.ones((chunk_size, chunk_size), dtype=np.uint8) * 255, mode="L"
                )
                tile = f"tiles/{dimension}/{zoom_level}/{x_level}/{y_level}.png"

                os.makedirs(os.path.dirname(tile), exist_ok=True)
                chunk.save(tile)


def update_image(coordinates, dimension="overworld"):
    os.makedirs(f"tiles/{dimension}", exist_ok=True)

    if len(coordinates) == 0:
        return

    center_offset = RESOLUTION // 2
    coordinates = sorted(coordinates, key=lambda coord: (coord[0], coord[1]))
    zoom_levels = sorted(os.listdir(f"tiles/{type}"), key=int)
    if not zoom_levels:
        return

    try:
        base_chunks_per_axis = max(1, RESOLUTION // MAX_CHUNK_SIZE)
        for zoom_level in zoom_levels:
            zoom_level = int(zoom_level)
            zoomed_resolution = RESOLUTION // (2**zoom_level)
            chunks_per_axis = base_chunks_per_axis * (2**zoom_level)
            chunk_size = zoomed_resolution // chunks_per_axis

            for x_level in range(chunks_per_axis):
                for y_level in range(chunks_per_axis):
                    tile = f"tiles/{dimension}/{zoom_level}/{x_level}/{y_level}.png"
                    tile_image = Image.open(tile)

                    for x, z in coordinates:
                        row = (x + center_offset) // chunk_size
                        col = (z + center_offset) // chunk_size

                        # check if the coordinates are within the current chunk
                        if not (x_level == row and y_level == col):
                            continue

                        pixel_x = x - (row * chunk_size - center_offset)
                        pixel_z = z - (col * chunk_size - center_offset)

                        # check if the pixel is within the chunk bounds
                        if 0 <= pixel_x < chunk_size and 0 <= pixel_z < chunk_size:
                            tile_image.putpixel((pixel_x, pixel_z), 0)

                    tile_image.save(tile)
                    tile_image.close()
    except Exception as e:
        raise e


def connect_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        return conn
    except Exception as e:
        print(e)
        return None


def get_coordinates_db(dimension="overworld"):
    coordinates = []
    dimension_path = {
        "overworld": OVERWORLD_PATH,
        "nether": NETHER_PATH,
        "end": END_PATH,
    }.get(dimension, OVERWORLD_PATH)

    conn = connect_db()
    if conn is None:
        return np.array(coordinates)

    try:
        with conn.cursor() as cursor, open(dimension_path, "a") as file:
            query = f"SELECT username, x, z FROM {dimension}"
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                username, x, z = row
                coordinates.append((round(x), round(z)))
                file.write(f"{username}, {x}, {z}\n")

            file.flush()
            query = f"TRUNCATE TABLE {dimension}"
            cursor.execute(query)
            conn.commit()

    except Exception as e:
        print(e)
    finally:
        conn.close()
        return np.array(coordinates)


def get_coordinates(dimension="overworld"):
    coordinates = []
    dimension_path = {
        "overworld": OVERWORLD_PATH,
        "nether": NETHER_PATH,
        "end": END_PATH,
    }.get(dimension, OVERWORLD_PATH)

    try:
        with open(dimension_path, "r") as file:
            if file.readline() is None:
                return np.array(coordinates)
            for line in file:
                username, x, z = map(str.strip, line.split(","))
                x = round(float(x))
                z = round(float(z))
                coordinates.append((x, z))
                file.flush()

    except Exception as e:
        print(e)
    finally:
        return np.array(coordinates)


def main():
    global RESOLUTION
    parser = argparse.ArgumentParser(
        description="Visualize minecraft player coordinates."
    )

    # positional
    parser.add_argument(
        "pos_mode",
        nargs="?",
        choices=["init", "update", "realtime"],
    )
    parser.add_argument(
        "pos_dimension",
        nargs="?",
        choices=["overworld", "nether", "end"],
    )
    parser.add_argument(
        "pos_zoom_level",
        nargs="?",
        type=int,
    )
    parser.add_argument(
        "pos_resolution",
        nargs="?",
        type=int,
    )

    # optional
    parser.add_argument(
        "--mode",
        choices=["init", "update", "realtime"],
        help="Modes: 'init' generates blank white images, 'update' updates the image with the coordinates, 'realtime' updates all the dimensions in realtime which has approx. 11-13s each operation (default: init)",
    )
    parser.add_argument(
        "--dimension",
        choices=["overworld", "nether", "end"],
        help="Dimension to generate/update the image for (default: overworld)",
    )
    parser.add_argument(
        "--zoom_level",
        type=int,
        help="Zoom level for the image (default: 1)",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=RESOLUTION,
        help=f"Resolution for the image (default: {RESOLUTION})",
    )

    args = parser.parse_args()
    mode = args.mode or args.pos_mode or "init"
    dimension = args.dimension or args.pos_dimension or "overworld"
    zoom_level = (
        args.zoom_level if args.zoom_level is not None else args.pos_zoom_level or 1
    )
    RESOLUTION = (
        args.resolution
        if args.resolution is not None
        else args.pos_resolution or RESOLUTION
    )

    if RESOLUTION > MAX_CHUNK_SIZE and (RESOLUTION & (RESOLUTION - 1)) != 0:
        print(
            f"resolution must be divisible by {MAX_CHUNK_SIZE}, and is even i.e. {MAX_CHUNK_SIZE}=1x1, {MAX_CHUNK_SIZE*2}=2x2"
        )
        return

    if mode == "realtime":
        try:
            while True:
                start_get = time.time()
                overworld_coordinates = get_coordinates_db("overworld")
                nether_coordinates = get_coordinates_db("nether")
                end_coordinates = get_coordinates_db("end")
                end_get = time.time()

                dimension_coordinates = {
                    "overworld": overworld_coordinates,
                    "nether": nether_coordinates,
                    "end": end_coordinates,
                }

                start_update = time.time()
                for dimension in dimension_coordinates:
                    coordinates = dimension_coordinates.get(
                        dimension, overworld_coordinates
                    )
                    update_image(coordinates, dimension)
                end_update = time.time()

                print(
                    f"o: {len(overworld_coordinates)} n: {len(nether_coordinates)} e: {len(end_coordinates)}\n"
                    f"get: {end_get - start_get:.2f}s update: {end_update - start_update:.2f}s"
                )

                time.sleep(1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            return

    elif mode == "update":
        coordinates = get_coordinates_db(dimension)
        update_image(coordinates, dimension)

    elif mode == "init":

        generate_image(dimension, zoom_level)

    else:
        print("invalid mode")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("total time taken: {:.2f} seconds".format(end_time - start_time))
