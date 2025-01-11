resolution = 8192;
center = {
    centerX: resolution / 2,
    centerY: -resolution / 2
}
// change based on how many zoom levels you have in i.e. tiles/type=overworld folder.
zoom = {
    min: 0,
    max: 4
}
let map;

function getMap() {
    // create the map
    map = L.map('map', {
        crs: L.CRS.Simple,
        minZoom: zoom.min,
        maxZoom: zoom.max,
        maxBounds: [[0, resolution], [-resolution, 0]],
        maxBoundsViscosity: 1.0
    }).setView([center.centerY, center.centerX], 0);
    return map;
}

function addTileLayer(map, tilesUrl) {
    // add the tiles to the map
    L.tileLayer(tilesUrl, {
        tileSize: resolution,
        noWrap: true
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

    map.on('mousemove', function(e) {
        const latlng = e.latlng;
        const x = Math.floor(latlng.lng);
        const y = Math.floor(latlng.lat);
        const offsetX = Math.floor(x - center.centerX);
        const offsetY = Math.floor(y - center.centerY);
        document.getElementById('x').textContent = offsetX;
        document.getElementById('y').textContent = offsetY;
    });
}

function addMarker(map, y, x, text='') {
    const marker = L.marker([y, x]).addTo(map);
    marker.bindPopup(text ? text : `${x}, ${y}`);
}

function selectTypeListener() {
    const select = document.getElementById('type');
    select.addEventListener('change', function() {
        if (map) map.remove();
        localStorage.setItem('selectedType', select.value);

        const type = select.value;
        const tilesUrl = `/tiles/${type}/{z}/{x}/{y}.png`;
        const newMap = getMap();
        addTileLayer(newMap, tilesUrl);
        displayCoordinates(newMap);
        // marks the center of the map
        addMarker(newMap, center.centerY, center.centerX, "0, 0");
    });

    const selectedType = localStorage.getItem('selectedType');
    if (selectedType) select.value = selectedType;

    select.dispatchEvent(new Event('change'));
}

function updateTiles() {
    const currentCenter = map.getCenter();
    const currentZoom = map.getZoom();
    const newTilesUrl = `/tiles/${document.getElementById('type').value}/{z}/{x}/{y}.png`;

    // remove all the current tiles
    map.eachLayer((layer) => {
        if (layer instanceof L.TileLayer) map.removeLayer(layer);
    });

    // add new tiles to the map
    addTileLayer(map, newTilesUrl);
    map.setView(currentCenter, currentZoom);
}

document.addEventListener('DOMContentLoaded', () => {
    selectTypeListener();
    setInterval(updateTiles, 10000);
});