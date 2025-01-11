# NOTE: This runs in the client.

import re
import subprocess
import threading

INTERVAL_SECONDS = 10
lock = threading.Lock()
overworld_path = "minecraft_overworld_player_coordinates.txt"
nether_path = "minecraft_the_nether_player_coordinates.txt"
end_path = "minecraft_the_end_player_coordinates.txt"

overworld_path_cumulative = "minecraft_overworld_player_coordinates_cumulative.txt"
nether_path_cumulative = "minecraft_the_nether_player_coordinates_cumulative.txt"
end_path_cumulative = "minecraft_the_end_player_coordinates_cumulative.txt"

# coordinates_path = r"C:\Users\yuane\AppData\Roaming\.minecraft\logs\latest.log"
coordinates_path = r"/mnt/c/Users/yuane/AppData/Roaming/.minecraft/logs/latest.log"
# coordinates_path = "latest.log"

def capture_coordinates_log():
    try:
        with open(overworld_path, "a") as overworld, open(nether_path, "a") as nether, open(end_path, "a") as end, open(overworld_path_cumulative, "a") as overworld_cumulative, open(nether_path_cumulative, "a") as nether_cumulative, open(end_path_cumulative, "a") as end_cumulative:
            with open(coordinates_path, "r") as file:
                file.seek(0, 2)
                while True:
                    line = file.readline()
                    if not line: continue

                    # CMAP paper_1_21_3164964 nidianazareno -46, -221
                    match = re.search(r"CMAP (\S+) (\S+) (-?\d+), (-?\d+)", line)
                    if not match: continue

                    try:
                        dimension, player, x, z = match.groups()
                        x, z = int(x), int(z)
                    except Exception as e:
                        print(e)
                        continue
                    
                    with lock:
                        if "nether" in dimension:
                            nether.write(f"{x}, {z}\n")
                            nether.flush()

                            nether_cumulative.write(f"{x}, {z}\n")
                            nether_cumulative.flush()
                        elif "end" in dimension:
                            end.write(f"{x}, {z}\n")
                            end.flush()

                            end_cumulative.write(f"{x}, {z}\n")
                            end_cumulative.flush()
                        else:
                            overworld.write(f"{x}, {z}\n")
                            overworld.flush()

                            overworld_cumulative.write(f"{x}, {z}\n")
                            overworld_cumulative.flush()

                    print(f"{x}, {z}")
    except Exception as e:
        print(e)

def force_endline_newline(file):
    try:
        with open(file, "a") as f:
            f.write("\n")
    except Exception as e:
        print(e)

def send_to_server():
    try:
        with lock:
            # add newline to the end of the file
            force_endline_newline(overworld_path)
            force_endline_newline(nether_path)
            force_endline_newline(end_path)

            # send the coordinates to the server
            command = """
            ssh -i ~/webhostvm.pem ubuntu@cmapinteractive.ddns.net 'cat >> ~/cmap/cmap_scripts/minecraft_overworld_player_coordinates.txt' < /mnt/c/Users/yuane/OneDrive/Documents/vscode/cmap/cmap_scripts/minecraft_overworld_player_coordinates.txt && \
            ssh -i ~/webhostvm.pem ubuntu@cmapinteractive.ddns.net 'cat >> ~/cmap/cmap_scripts/minecraft_the_nether_player_coordinates.txt' < /mnt/c/Users/yuane/OneDrive/Documents/vscode/cmap/cmap_scripts/minecraft_the_nether_player_coordinates.txt && \
            ssh -i ~/webhostvm.pem ubuntu@cmapinteractive.ddns.net 'cat >> ~/cmap/cmap_scripts/minecraft_the_end_player_coordinates.txt' < /mnt/c/Users/yuane/OneDrive/Documents/vscode/cmap/cmap_scripts/minecraft_the_end_player_coordinates.txt
            """
            result = subprocess.run(command, shell=True, check=True)

            if result.returncode == 0:
                # after executing truncate the files
                open(overworld_path, "w").close()
                open(nether_path, "w").close()
                open(end_path, "w").close()
            else:
                print(result)

    except Exception as e:
        print(e)

# start the thread
threading.Thread(target=capture_coordinates_log, daemon=True).start()
while True:
    send_to_server()
    threading.Event().wait(INTERVAL_SECONDS)