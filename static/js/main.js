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
let mtimeMsCache = {};
const playerMarkers = {};
let followedPlayer = null;

const playerIcon = L.icon({
    iconUrl: '/images/Player.png',
    iconSize: [32, 32],
    className: 'map-icon player-icon'
});

const compassIcon = L.icon({
    iconUrl: '/images/Compass.png',
    iconSize: [32, 32],
    className: 'map-icon compass-icon'
});

// override createTile from TileLayer.js to add conditional cache busting.
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
            let mtimeMs = mtimeMsCache[tileUrl];

            if (!mtimeMs) {
                mtimeMs = await getMTimeMs(tileUrl);
                if (mtimeMs) setMtimeMsCache(tileUrl, mtimeMs);
            }
            tile.src = mtimeMs ? `${tileUrl}?mtimeMs=${mtimeMs}` : tileUrl;
        })();
        return tile;
    },
});

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

function createToast({
    imgSrc = '...',
    playerName = 'Player',
    message = 'Joined the game',
    toastId = `toast-${Date.now()}`,
} = {}) {
    const $container = $('.toast-container');
    const $toast = $(
        `<div class="toast" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}">
            <div class="toast-header rounded-bottom">
                <img src="${imgSrc}" class="rounded me-2" alt="${playerName}" width="32" height="32">
                <strong class="me-auto">${playerName}</strong>
                <small class="text-body-secondary">${message}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>`
    );
    $container.append($toast);
    const toast = bootstrap.Toast.getOrCreateInstance($toast[0]);
    toast.show();
}

function createPlayerContextMenu() {

}

function createMapContextMenu(e) {
    e.preventDefault();
    const $contextMenu = $('#contextMenu');
    const $copyCoordinatesBtn = $('#copyCoordinatesBtn');
    const $copyTileBtn = $('#copyTileBtn');

    const coordinates = `X: ${$('#x').text()} Z: ${$('#z').text()}`;
    const tile = `TILE: ${$('#tileX').text()} ${$('#tileY').text()}`;

    $copyCoordinatesBtn.text(coordinates);
    $copyTileBtn.text(tile);
    $copyCoordinatesBtn.attr('title', 'Copy coordinates to clipboard');
    $copyTileBtn.attr('title', 'Copy tile to clipboard');

    $contextMenu.css({
        top: e.pageY + 'px',
        left: e.pageX + 'px',
    }).removeClass('hidden');

    $contextMenu.on('click', function (e) {
        e.stopPropagation();
    });

    $(document).on('click', function () {
        $contextMenu.addClass('hidden');
    });

    $copyCoordinatesBtn.on('click', function () {
        navigator.clipboard.writeText(coordinates).then(() => {
            createToast({
                imgSrc: '/images/Link.svg',
                playerName: 'Coordinates copied to clipboard',
                message: '',
            });
        });
    });
    $copyTileBtn.on('click', function () {
        navigator.clipboard.writeText(tile).then(() => {
            createToast({
                imgSrc: '/images/Link.svg',
                playerName: 'Tile copied to clipboard',
                message: '',
            });
        });
    });
}

function getTileCoordinates(mapX, mapY, zoomlevel) {
    const tileX = Math.floor(mapX / MAX_CHUNK_SIZE);
    const tileY = -Math.floor(mapY / MAX_CHUNK_SIZE) - 1;
    return { x: tileX, y: tileY, z: zoomlevel };
}

function setMtimeMsCache(key, value) {
    mtimeMsCache[key] = value;
}

async function getMTimeMs(tileUrl) {
    const key = tileUrl.split('/').slice(2, 7).join('/');
    const response = await fetch(`/tiles-mtimeMs/${key}`);
    if (response.status === 200) return await response.text();
}

function createMapInstance() {
    // create the map
    map = L.map('map', {
        crs: L.CRS.Simple,
        minZoom: zoom.min,
        maxZoom: zoom.max,
        zoomControl: false,
        maxBounds: [[0, RESOLUTION], [-RESOLUTION, 0]],
        maxBoundsViscosity: 0.7,
        attributionControl: false,
    }).setView([center.centerY, center.centerX], 0);
}

function addTileLayer(tilesUrl) {
    if (tileLayer) map.removeLayer(tileLayer);

    tileLayer = new SmartTileLayer(tilesUrl, {
        MAX_CHUNK_SIZE: MAX_CHUNK_SIZE,
        noWrap: true,
    }).addTo(map);
}

function displayCoordinates() {
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

    // display the tile of the clicked coordinates
    // map.on('click', function(e) {
    //     const latlng = e.latlng;
    //     const x = Math.floor(latlng.lng);
    //     const y = Math.floor(latlng.lat);
    //     alert(`X: ${Math.floor(x / MAX_CHUNK_SIZE)}, Y: ${Math.floor(-y / MAX_CHUNK_SIZE)}`);
    // });

    map.on('mousemove', function (e) {
        const latlng = e.latlng;
        const x = Math.floor(latlng.lng);
        const y = Math.floor(latlng.lat);
        document.getElementById('x').textContent = Math.floor(x - center.centerX);
        document.getElementById('z').textContent = -Math.floor(y - center.centerY);
        document.getElementById('tileX').textContent = Math.floor(x / MAX_CHUNK_SIZE);
        document.getElementById('tileY').textContent = Math.floor(-y / MAX_CHUNK_SIZE);
    });
}

function addMarker(icon, y, x, title, text = '') {
    let marker = L.marker([y, x]).addTo(map);
    if (icon) marker.setIcon(icon);
    if (title) marker._icon.title = title;
    marker.bindPopup(text ? text : `${x}, ${y}`);
    return marker;
}

function dimensionTypeListener() {
    const select = document.getElementById('dimensionType');
    select.addEventListener('change', function () {
        if (map) map.remove();

        Object.values(playerMarkers).forEach(marker => map && map.removeLayer(marker));
        Object.keys(playerMarkers).forEach(key => delete playerMarkers[key]);

        localStorage.setItem('dimensionType', select.value);

        const tilesUrl = `/tiles/${worldName}/${select.value}/{z}/{x}/{y}.png`;

        createMapInstance();
        addTileLayer(tilesUrl);
        displayCoordinates();

        // marks the center of the map
        addMarker(compassIcon, center.centerY, center.centerX, "spawn", "0, 0");
    });

    const dimensionType = localStorage.getItem('dimensionType');
    if (dimensionType) select.value = dimensionType;

    select.dispatchEvent(new Event('change'));
}

function updateOrAddPlayerMarker(playerName, dimension, mapX, mapY, x, z, zoomlevel) {
    const select = document.getElementById('dimensionType');
    const playerMarker = playerMarkers[playerName];

    if (dimension !== localStorage.getItem('dimensionType')) {
        map.removeLayer(playerMarker);
        delete playerMarkers[playerName];

        if (followedPlayer === playerName) {
            select.value = dimension;
            select.dispatchEvent(new Event('change'));
            localStorage.setItem('dimensionType', dimension);
        }
        return;
    }
    if (playerMarker) playerMarker.setLatLng([mapY, mapX]);
    else {
        const marker = addMarker(playerIcon, mapY, mapX, playerName, `${playerName}<br>x: ${x}, z: ${z}`);
        playerMarkers[playerName] = marker;

        marker.on('dblclick', () => {
            // toggle follow player on double click
            if (followedPlayer === playerName) followedPlayer = null;
            else followedPlayer = playerName;
            map.setView([mapY, mapX], zoomlevel, { animate: true });
        });
    }
    // always focus on the player marker
    if (followedPlayer === playerName) map.setView([mapY, mapX], zoomlevel, { animate: true });
}

async function refreshTile(mapX, mapY, zoomlevel) {
    const tileCoords = getTileCoordinates(mapX, mapY, zoomlevel);
    const tileUrl = tileLayer.getTileUrl(tileCoords);
    const oldMtimeMs = mtimeMsCache[tileUrl];
    const mtimeMs = await getMTimeMs(tileUrl);

    const tileKey = `${tileCoords.x}:${tileCoords.y}:${tileCoords.z}`;
    const tileObj = tileLayer._tiles[tileKey];

    if (tileObj && tileObj.el) {
        const tile = tileObj.el;
        // conditional cache busting
        if (mtimeMs && mtimeMs !== oldMtimeMs) {
            setMtimeMsCache(tileUrl, mtimeMs);
            tile.src = `${tileUrl}?mtimeMs=${mtimeMs}`;
        }
    }
}

async function updatePlayerMarkers() {
    try {
        const response = await fetch(`/players-coordinates?world=${worldName}`);
        if (!response.ok) return console.error('Error fetching player coordinates');

        const data = await response.json();
        const zoomlevel = map.getZoom();

        for (const { player_name, x, z, dimension } of data) {
            const mapX = x + center.centerX;
            const mapY = -z + center.centerY;

            updateOrAddPlayerMarker(player_name, dimension, mapX, mapY, x, z, zoomlevel);
            await refreshTile(mapX, mapY, zoomlevel);
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
    mapContainer.addEventListener('mousedown', (e) => {
        if (e.button === 0) {
            mapContainer.style.cursor = 'grabbing';
            handlePanning();
        }
    });
    mapContainer.addEventListener('mouseup', (e) => {
        if (e.button === 0) {
            mapContainer.style.cursor = 'grab';
            handlePanEnd();
        }
    });
    downloadButton.addEventListener('click', handleDownload);
    mapContainer.addEventListener('contextmenu', createMapContextMenu);
}

document.addEventListener('DOMContentLoaded', () => {
    eventListener();
    dimensionTypeListener();
    startUpdateTileInterval();
});