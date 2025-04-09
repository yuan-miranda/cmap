const RESOLUTION = 32768;
// const MAX_CHUNK_SIZE = 8192;
const MAX_CHUNK_SIZE = 256;

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
    if (tileLayer) {
        map.removeLayer(tileLayer);
    }

    tileLayer = L.tileLayer(tilesUrl, {
        MAX_CHUNK_SIZE: MAX_CHUNK_SIZE,
        noWrap: true,
    }).addTo(map);
}
// function addTileLayer(map, tilesUrl) {
//     // add the tiles to the map
//     L.tileLayer(tilesUrl, {
//         MAX_CHUNK_SIZE: MAX_CHUNK_SIZE,
//         noWrap: true
//     }).addTo(map);
// }

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

    map.on('mousemove', function(e) {
        const latlng = e.latlng;
        const x = Math.floor(latlng.lng);
        const y = Math.floor(latlng.lat);
        const offsetX = Math.floor(x - center.centerX);
        const offsetY = Math.floor(y - center.centerY);
        document.getElementById('x').textContent = offsetX;
        document.getElementById('z').textContent = -offsetY;
    });
}

function addMarker(map, y, x, text='') {
    const marker = L.marker([y, x]).addTo(map);
    marker.bindPopup(text ? text : `${x}, ${y}`);
}

function dimensionTypeListener() {
    const select = document.getElementById('type');
    select.addEventListener('change', function() {
        if (map) map.remove();
        localStorage.setItem('dimensionType', select.value);

        const tilesUrl = `/tiles/${select.value}/{z}/{x}/{y}.png`;
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

function updateTiles() {
    const timestamp = new Date().getTime();
    const newTilesUrl = `/tiles/${document.getElementById('type').value}/{z}/{x}/{y}.png?${timestamp}`;
    
    // update the tile layer URL
    if (tileLayer) tileLayer.setUrl(newTilesUrl);
}
// function updateTiles() {
//     const currentCenter = map.getCenter();
//     const currentZoom = map.getZoom();
//     const timestamp = new Date().getTime();
//     const newTilesUrl = `/tiles/${document.getElementById('type').value}/{z}/{x}/{y}.png?${timestamp}`;

//     // remove all the current tiles
//     map.eachLayer((layer) => {
//         if (layer instanceof L.TileLayer) map.removeLayer(layer);
//     });

//     // add new tiles to the map
//     addTileLayer(map, newTilesUrl);
//     map.setView(currentCenter, currentZoom);
// }

document.addEventListener('DOMContentLoaded', () => {
    dimensionTypeListener();
    setInterval(updateTiles, 10000);
});