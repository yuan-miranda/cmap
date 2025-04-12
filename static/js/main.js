// "node_modules/leaflet/src/layer/tile/TileLayer.js"

const RESOLUTION = 32768 / 4;
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
const mtimeMsCache = {};

async function getMTimeMs(tileUrl) {
    // Array(7) [ "", "tiles", "world", "overworld", "0", "30", "17.png" ]
    const key = tileUrl.split('/').slice(2, 7).join('/');
    const response = await fetch(`/tiles-mtimeMs/${key}`);
    if (response.status === 200) {
        const mtimeMs = await response.text();
        mtimeMsCache[key] = mtimeMs;
        return mtimeMs;
    }

}

const SmartTileLayer = L.TileLayer.extend({
    createTile: function (coords, done) {
        var tile = document.createElement('img');

        L.DomEvent.on(tile, 'load', L.Util.bind(this._tileOnLoad, this, done, tile));
        L.DomEvent.on(tile, 'error', L.Util.bind(this._tileOnError, this, done, tile));

        if (this.options.crossOrigin || this.options.crossOrigin === '') {
            tile.crossOrigin = this.options.crossOrigin === true ? '' : this.options.crossOrigin;
        }

        // for this new option we follow the documented behavior
        // more closely by only setting the property when string
        if (typeof this.options.referrerPolicy === 'string') {
            tile.referrerPolicy = this.options.referrerPolicy;
        }

        // The alt attribute is set to the empty string,
        // allowing screen readers to ignore the decorative image tiles.
        // https://www.w3.org/WAI/tutorials/images/decorative/
        // https://www.w3.org/TR/html-aria/#el-img-empty-alt
        tile.alt = '';

        (async () => {
            const tileUrl = this.getTileUrl(coords);
            const mtimeMs = mtimeMsCache[tileUrl] || await getMTimeMs(tileUrl);
            if (mtimeMs) {
                tile.src = `${tileUrl}?mtimeMs=${mtimeMs}`;
            }
            else {
                tile.src = tileUrl;
            }
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
        maxBoundsViscosity: 0.7
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

function updateTilesInterval() {
    if (tileLayer) tileLayer.redraw();
}

function startUpdateTileInterval() {
    intervalId = setInterval(updateTilesInterval, 5000);
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
    // when left mouse is down and is inside the map
    const mapContainer = document.getElementById('map');
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
}


document.addEventListener('DOMContentLoaded', () => {
    eventListener();
    dimensionTypeListener();
    startUpdateTileInterval();
});