## Coordinate Mapper (cmap)
Visualize minecraft player coordinates generated from the coordinates [cmap-paper](https://github.com/yuan-miranda/cmap-paper) sent using Leaflet.js for rendering the image tiles on the website. This is similar to [2b2t Nocom heatmap](https://en.m.wikipedia.org/wiki/File:2b2t_Nocom_Overworld_Heatmap.png), but with each coordinate represented as a dot and not being a heatmap.

> [realtimeChunkImage.py](https://github.com/yuan-miranda/cmap/blob/main/cmap_scripts/realtimeChunkImage.py) main script.<br>
> [app.js](https://github.com/yuan-miranda/cmap/blob/main/app.js) backend of the page.

![image](https://github.com/user-attachments/assets/6e80245e-7aec-4682-ae87-67823a50fdd5)
Example map taken from [here](http://cmapinteractive.ddns.net/)

This repository has 2 main folders:
1. **cmap_minecraft**: Source code for the cmap plugin. See the [repository](https://github.com/yuan-miranda/cmap-paper).
2. **cmap_scripts**: Cmap related python scripts.

## Usage (realtimeChunkImage.py)
Generates blank white images. Each zoom_level the quality of the image doesnt increase, the number of tiles does.
```
py realtimeChunkImage.py init [<type=OVERWORLD | nether | end> <zoom_level=1>]
```
Updates the image with the coordinates. The coordinates are black pixels on the image.
```
py realtimeChunkImage.py update [<type=OVERWORLD | nether | end>]\n
```
Update the entire overworld, nether, end tiles in realtime (approx. 11-13s each operation)
```
py realtimeChunkImage.py realtime
```

## Example Commands
| Command                       | Operation                                                                                           |
|-------------------------------|-----------------------------------------------------------------------------------------------------|
| py realtimeChunkImage.py init | initialize blank white tiles (overworld)                                                        |
| py realtimeChunkImage.py init end | specify the tiles to make                                                                   |
| py realtimeChunkImage.py init end 2 | make tiles for end with 2 zoom level (for leaflet)                                        |
| py realtimeChunkImage.py update | update the image with the coords from the coordinate files (overworld, along the zoom levels) |
| py realtimeChunkImage.py update nether | update the nether tiles only                                                           |
| py realtimeChunkImage.py realtime | update the entire overworld, nether, end tiles in realtime                                  |

## Installation Setup
Note: You must have `Git`, `Python 3` or above, `Node.js` and `npm` installed prior to this setup.
1. Clone the repository on your machine:
```
git clone https://github.com/yuan-miranda/cmap.git
```
2. Install the following
```
npm install leaflet
pip install pillow numpy matplotlib
```
3. Run this schema on your PostgreSQL (pgAdmin4)
```SQL
CREATE TABLE IF NOT EXISTS overworld (
    id SERIAL PRIMARY KEY,
    x INT NOT NULL,
    z INT NOT NULL
);

CREATE TABLE IF NOT EXISTS nether (
    id SERIAL PRIMARY KEY,
    x INT NOT NULL,
    z INT NOT NULL
);

CREATE TABLE IF NOT EXISTS the_end (
    id SERIAL PRIMARY KEY,
    x INT NOT NULL,
    z INT NOT NULL
);
```
4. Setup the database details (realtimeChunkImage.py)
```Python
DB_HOST = ""
DB_PORT = 5432
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = ""
```
5. Run the interactive map
```
node app.js
```
6. Generate the tiles for overworld, nether, end with no zoom
```
cd cmap_scripts
py realtimeChunkImage.py init overworld
py realtimeChunkImage.py init nether
py realtimeChunkImage.py init end
```
7. Run the realtimeChunkImage.py in realtime (assuming you have the tiles generated)
```
cd cmap_scripts
py realtimeChunkImage.py realtime
```
   - after doing the procedures, it should look like this (example output)
![image](https://github.com/user-attachments/assets/28a8b820-8d84-485b-907a-c5bf37547742)

## Acknowledgments
- [ChatGPT](https://chatgpt.com/)
- [Nocom](https://2b2t.miraheze.org/wiki/Nocom)
- [Interactive game map](https://wuthering-waves-map.appsample.com/)
