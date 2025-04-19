import numpy as np
import time
from PIL import Image
import sys
import os
import psycopg2
import argparse
from dotenv import load_dotenv

load_dotenv()
Image.MAX_IMAGE_PIXELS = None

# north is down
# east is right

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
if (
    DB_HOST is None
    or DB_PORT is None
    or DB_NAME is None
    or DB_USER is None
    or DB_PASSWORD is None
):
    print(
        "DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD must be set in .env file or environment variables"
    )
    sys.exit(1)

RESOLUTION = 32768
MAX_CHUNK_SIZE = 256
# MAX_CHUNK_SIZE = 8192

WORLD_NAME = "world"
WORLD_DIR = None
OVERWORLD_PATH = None
NETHER_PATH = None
END_PATH = None

OVERWORLD_TILES_PATH = None
NETHER_TILES_PATH = None
END_TILES_PATH = None


def generate_image(dimension="overworld", zoom_levels=1):
    dimension_tiles_path = {
        "overworld": OVERWORLD_TILES_PATH,
        "nether": NETHER_TILES_PATH,
        "the_end": END_TILES_PATH,
    }.get(dimension, OVERWORLD_TILES_PATH)
    os.makedirs(dimension_tiles_path, exist_ok=True)

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
                tile = f"{dimension_tiles_path}/{zoom_level}/{x_level}/{y_level}.png"

                os.makedirs(os.path.dirname(tile), exist_ok=True)
                chunk.save(tile)


def update_image(coordinates, dimension="overworld"):
    dimension_tiles_path = {
        "overworld": OVERWORLD_TILES_PATH,
        "nether": NETHER_TILES_PATH,
        "the_end": END_TILES_PATH,
    }.get(dimension, OVERWORLD_TILES_PATH)
    os.makedirs(dimension_tiles_path, exist_ok=True)

    if len(coordinates) == 0:
        return

    center_offset = RESOLUTION // 2
    coordinates = sorted(coordinates, key=lambda coord: (coord[0], coord[1]))
    zoom_levels = sorted(os.listdir(dimension_tiles_path), key=int)
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
                    tile = (
                        f"{dimension_tiles_path}/{zoom_level}/{x_level}/{y_level}.png"
                    )
                    tile_image = Image.open(tile)
                    isUpdated = False

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
                            isUpdated = True

                    if isUpdated:
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
        "the_end": END_PATH,
    }.get(dimension, OVERWORLD_PATH)
    os.makedirs(os.path.dirname(dimension_path), exist_ok=True)

    conn = connect_db()
    if conn is None:
        return np.array(coordinates)

    try:
        with conn.cursor() as cursor, open(dimension_path, "a") as file:
            query = f"SELECT player_name, x, z FROM {dimension}"
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                parts = list(map(str.strip, row))
                if len(parts) == 3:
                    player_name, x, z = parts
                else:
                    x, z = row
                coordinates.append((round(float(x)), round(float(z))))
                file.write(
                    f"{player_name}, {x}, {z}\n" if len(parts) == 3 else f"{x}, {z}\n"
                )

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
        "the_end": END_PATH,
    }.get(dimension, OVERWORLD_PATH)
    os.makedirs(os.path.dirname(dimension_path), exist_ok=True)

    try:
        with open(dimension_path, "r") as file:
            if file.readline() is None:
                return np.array(coordinates)
            for line in file:
                parts = list(map(str.strip, line.split(",")))
                if len(parts) == 3:
                    player_name, x, z = parts
                else:
                    x, z = parts
                coordinates.append((round(float(x)), round(float(z))))
                file.flush()

    except Exception as e:
        print(e)
    finally:
        return np.array(coordinates)


def eval_resolution(expr):
    allowed_globals = {"__builtins__": None}
    allowed_locals = {}

    try:
        result = eval(expr, allowed_globals, allowed_locals)
        return int(result)
    except Exception as e:
        raise argparse.ArgumentTypeError(
            f"Invalid resolution expression: {expr}. Error: {e}"
        )


def main():
    global RESOLUTION, WORLD_NAME, OVERWORLD_PATH, NETHER_PATH, END_PATH, OVERWORLD_TILES_PATH, NETHER_TILES_PATH, END_TILES_PATH
    parser = argparse.ArgumentParser(
        description="Visualize minecraft player coordinates."
    )

    # positional
    parser.add_argument(
        "pos_mode",
        nargs="?",
        choices=["init", "update", "realtime"],
    )
    # world name or the server name of the user
    parser.add_argument(
        "pos_world",
        nargs="?",
        default=WORLD_NAME,
    )
    parser.add_argument(
        "pos_dimension",
        nargs="?",
        choices=["overworld", "nether", "the_end", "all"],
    )

    # optional
    parser.add_argument(
        "--mode",
        choices=["init", "update", "realtime"],
        help="Modes: 'init' generates blank white images, 'update' updates the image with the coordinates, 'realtime' updates all the dimensions in realtime which has approx. 1s each operation (default: init)",
    )
    parser.add_argument(
        "--world",
        default=WORLD_NAME,
        help="World name or server name (default: world)",
    )
    parser.add_argument(
        "--dimension",
        choices=["overworld", "nether", "the_end", "all"],
        help="Dimension to generate/update the image for (default: overworld)",
    )
    parser.add_argument(
        "--zoom_level",
        type=int,
        help="Zoom level for the image (default: 1)",
    )
    parser.add_argument(
        "--resolution",
        type=eval_resolution,
        default=RESOLUTION,
        help=f"Resolution for the image (default: {RESOLUTION})",
    )
    parser.add_argument(
        "--readfrom",
        choices=["db", "file"],
        default="db",
        help="Read coordinates from database or file (default: db)",
    )

    args = parser.parse_args()
    mode_arg = args.pos_mode or args.mode or "init"
    world_name_arg = args.pos_world or args.world or WORLD_NAME
    dimension_arg = args.pos_dimension or args.dimension or "overworld"
    zoom_level = args.zoom_level or 1
    resolution_arg = args.resolution or RESOLUTION
    readfrom_arg = args.readfrom or "db"

    RESOLUTION = resolution_arg
    WORLD_NAME = world_name_arg
    WORLD_DIR = f"worlds/{WORLD_NAME}"

    OVERWORLD_PATH = f"{WORLD_DIR}/overworld.txt"
    NETHER_PATH = f"{WORLD_DIR}/nether.txt"
    END_PATH = f"{WORLD_DIR}/the_end.txt"

    OVERWORLD_TILES_PATH = f"tiles/{WORLD_NAME}/overworld"
    NETHER_TILES_PATH = f"tiles/{WORLD_NAME}/nether"
    END_TILES_PATH = f"tiles/{WORLD_NAME}/the_end"

    if RESOLUTION > MAX_CHUNK_SIZE and (RESOLUTION & (RESOLUTION - 1)) != 0:
        print(
            f"Resolution must be divisible by {MAX_CHUNK_SIZE}, and is even i.e. {MAX_CHUNK_SIZE}=1x1, {MAX_CHUNK_SIZE*2}=2x2"
        )
        return

    if mode_arg == "realtime":
        if dimension_arg == "all":
            print(
                f"'{mode_arg}' mode already updates all dimensions. Ignoring '{dimension_arg}' argument."
            )

        try:
            while True:
                start_get = time.time()
                dimensions = ["overworld", "nether", "the_end"]
                dimension_coordinates = {
                    dim: get_coordinates_db(dim) for dim in dimensions
                }
                end_get = time.time()

                start_update = time.time()
                for dimension, coordinates in dimension_coordinates.items():
                    update_image(coordinates, dimension)
                end_update = time.time()

                print(
                    f"o: {len(dimension_coordinates['overworld'])} n: {len(dimension_coordinates['nether'])} e: {len(dimension_coordinates['the_end'])}\n"
                    f"get: {end_get - start_get:.2f}s update: {end_update - start_update:.2f}s"
                )

                time.sleep(1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            return

    elif mode_arg == "update":
        dimensions = (
            ["overworld", "nether", "the_end"]
            if dimension_arg == "all"
            else [dimension_arg]
        )
        for dimension in dimensions:
            coordinates = (
                get_coordinates_db(dimension)
                if readfrom_arg == "db"
                else get_coordinates(dimension)
            )
            update_image(coordinates, dimension)

    elif mode_arg == "init":
        dimensions = (
            ["overworld", "nether", "the_end"]
            if dimension_arg == "all"
            else [dimension_arg]
        )
        for dimension in dimensions:
            generate_image(dimension, zoom_level)


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("Total time taken: {:.2f} seconds".format(end_time - start_time))
