
const RESOLUTION = 32768;
const MAX_CHUNK_SIZE = 256;
// const MAX_CHUNK_SIZE = 8192;

const center = {
    centerX: RESOLUTION / 2,
    centerY: -RESOLUTION / 2
}

// zoom level are the numerical folder inside /tiles
// i.e. /tiles/0, /tiles/1
const zoom = {
    min: 0,
    max: 0
}
let map;
let tileLayer;
let worldName = 'world';
let intervalId;
let mtimeMsCache = JSON.parse(localStorage.getItem('mtimeMsCache') || '{}');
const playerMarkers = {};

async function handleDownload() {
    const world = localStorage.getItem('worldName') || worldName;
    const dimensionType = localStorage.getItem('dimensionType') || 'overworld';

    try {
        const response = await fetch(`/download-coordinates-log?world=${world}&dimension=${dimensionType}`);
        if (!response.ok) return alert('Error downloading file');
    
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${world}-${dimensionType}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error:', error);
    }
}

function getTileCoordinates(mapX, mapY, zoomlevel) {
    const tileX = Math.floor(mapX / MAX_CHUNK_SIZE);
    const tileY = -Math.floor(mapY / MAX_CHUNK_SIZE);
    return { x: tileX, y: tileY, z: zoomlevel };
}

function setMtimeMsCache(key, value) {
    mtimeMsCache[key] = value;
    localStorage.setItem('mtimeMsCache', JSON.stringify(mtimeMsCache));
}

async function getMTimeMs(tileUrl) {
    const key = tileUrl.split('/').slice(2, 7).join('/');
    const response = await fetch(`/tiles-mtimeMs/${key}`);
    if (response.status === 200) return await response.text();
}

// override createTile from TileLayer.js to add mtimeMs to the tile url.
// mtimeMs is a cache buster for the browser, it stays the same so long
// as the tile is not modified hence the name mtimeMs.
const SmartTileLayer = L.TileLayer.extend({
    createTile: function (coords, done) {
        var tile = document.createElement('img');

        L.DomEvent.on(tile, 'load', L.Util.bind(this._tileOnLoad, this, done, tile));
        L.DomEvent.on(tile, 'error', L.Util.bind(this._tileOnError, this, done, tile));

        if (this.options.crossOrigin || this.options.crossOrigin === '') {
            tile.crossOrigin = this.options.crossOrigin === true ? '' : this.options.crossOrigin;
        }

        if (typeof this.options.referrerPolicy === 'string') {
            tile.referrerPolicy = this.options.referrerPolicy;
        }

        tile.alt = '';

        // adds mtimeMs to the tile url
        (async () => {
            const tileUrl = this.getTileUrl(coords);
            const mtimeMs = mtimeMsCache[tileUrl] || await getMTimeMs(tileUrl);
            if (mtimeMs) tile.src = `${tileUrl}?mtimeMs=${mtimeMs}`;
            else tile.src = tileUrl;
        })();
        return tile;
    },
});

function getMap() {
    // create the map
    map = L.map('map', {
        crs: L.CRS.Simple,
        minZoom: zoom.min,
        maxZoom: zoom.max,
        maxBounds: [[0, RESOLUTION], [-RESOLUTION, 0]],
        maxBoundsViscosity: 0.7,
        attributionControl: false,
    }).setView([center.centerY, center.centerX], 0);
    return map;
}

function addTileLayer(map, tilesUrl) {
    if (tileLayer) map.removeLayer(tileLayer);

    tileLayer = new SmartTileLayer(tilesUrl, {
        MAX_CHUNK_SIZE: MAX_CHUNK_SIZE,
        noWrap: true,
    }).addTo(map);
}

function displayCoordinates(map) {
    // display coordinates on click
    // map.on('click', function(e) {
    //     const latlng = e.latlng;
    //     const x = Math.floor(latlng.lng);
    //     const y = Math.floor(latlng.lat);
    //     const offsetX = Math.floor(x - center.centerX);
    //     const offsetY = Math.floor(y - center.centerY);
    //     alert(`X: ${offsetX}, Y: ${offsetY}`);
    //     console.log(`X: ${offsetX}, Y: ${offsetY}`);
    // });

    map.on('mousemove', function (e) {
        const latlng = e.latlng;
        const x = Math.floor(latlng.lng);
        const y = Math.floor(latlng.lat);
        const offsetX = Math.floor(x - center.centerX);
        const offsetY = Math.floor(y - center.centerY);
        document.getElementById('x').textContent = offsetX;
        document.getElementById('z').textContent = -offsetY;
    });
}

function addMarker(map, y, x, text = '') {
    const marker = L.marker([y, x]).addTo(map);
    marker.bindPopup(text ? text : `${x}, ${y}`);
}

function dimensionTypeListener() {
    const select = document.getElementById('dimensionType');
    select.addEventListener('change', function () {
        if (map) map.remove();
        localStorage.setItem('dimensionType', select.value);

        const tilesUrl = `/tiles/${worldName}/${select.value}/{z}/{x}/{y}.png`;
        const newMap = getMap();

        addTileLayer(newMap, tilesUrl);
        displayCoordinates(newMap);

        // marks the center of the map
        addMarker(newMap, center.centerY, center.centerX, "0, 0");
    });

    const dimensionType = localStorage.getItem('dimensionType');
    if (dimensionType) select.value = dimensionType;

    select.dispatchEvent(new Event('change'));
}

async function updatePlayerMarkers() {
    const dimensionType = localStorage.getItem('dimensionType') || 'overworld';

    try {
        const response = await fetch(`/players-coordinates?world=${worldName}&dimension=${dimensionType}`);
        if (!response.ok) return console.error('Error fetching player coordinates');

        const data = await response.json();
        
        const zoomlevel = map.getZoom();

        for (const player of data) {
            const { player_name, x, z } = player;
            const mapX = x + center.centerX;
            const mapY = -z + center.centerY;

            const playerMarker = playerMarkers[player_name];
            if (playerMarker) playerMarker.setLatLng([mapY, mapX]);
            else {
                const marker = L.marker([mapY, mapX]).addTo(map);
                marker.bindPopup(`${player_name}<br>x: ${x}, z: ${z}`);
                playerMarkers[player_name] = marker;
            }

            // determine the tile this marker is in
            const tileCoords = getTileCoordinates(mapX, mapY, zoomlevel);
            const tileUrl = tileLayer.getTileUrl(tileCoords);
            const oldMtimeMs = mtimeMsCache[tileUrl];
            const mtimeMs = await getMTimeMs(tileUrl);

            const tileKey = `${tileCoords.x}:${tileCoords.y}:${tileCoords.z}`;
            const tileObj = tileLayer._tiles[tileKey];

            if (tileObj && tileObj.el) {
                const tile = tileObj.el;
                if (mtimeMs && mtimeMs !== oldMtimeMs) {
                    setMtimeMsCache(tileUrl, mtimeMs);
                    tile.src = `${tileUrl}?mtimeMs=${mtimeMs}`;
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function startUpdateTileInterval() {
    intervalId = setInterval(() => {
        updatePlayerMarkers();
    }, 1000);
}

function stopUpdateTileInterval() {
    clearInterval(intervalId);
}

function handlePanning() {
    stopUpdateTileInterval();
}

function handlePanEnd() {
    startUpdateTileInterval();
}

function eventListener() {
    const mapContainer = document.getElementById('map');
    const downloadButton = document.getElementById('downloadFileButton');
    mapContainer.addEventListener('mousedown', function (e) {
        if (e.button === 0) {
            mapContainer.style.cursor = 'grabbing';
            handlePanning();
        }
    });

    mapContainer.addEventListener('mouseup', function (e) {
        if (e.button === 0) {
            mapContainer.style.cursor = 'grab';
            handlePanEnd();
        }
    });

    downloadButton.addEventListener('click', handleDownload);

}

document.addEventListener('DOMContentLoaded', () => {
    eventListener();
    dimensionTypeListener();
    startUpdateTileInterval();
});