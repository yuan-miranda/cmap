const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const app = express();
const port = 3000;

app.use(express.static(path.join(__dirname, 'static')));
app.use("/node_modules", express.static(path.join(__dirname, 'node_modules')));
app.use("/images", express.static(path.join(__dirname, 'images')));
app.use("/worlds", express.static(path.join(__dirname, 'worlds')));

app.get('/', (req, res) => {
    res.sendFile("static/html/index.html", { root: __dirname });
});

app.get("/tiles/:world/:dimension/:z/:x/:y.png", (req, res) => {
    const { world, dimension, z, x, y } = req.params;
    const tilePath = path.join(__dirname, 'tiles', world, dimension, z, `${x}/${y}.png`);

    fs.stat(tilePath, (err, stats) => {
        if (err) return res.status(404).send(err.message);

        const etag = `"${stats.mtimeMs}"`;
        if (req.headers['if-none-match'] === etag) return res.status(304).send('Not Modified');

        res.setHeader('ETag', etag);
        res.setHeader('Cache-Control', 'public, max-age=3600, must-revalidate');

        res.sendFile(tilePath);
    });
});

app.get("/tiles-mtimeMs/:world/:dimension/:z/:x/:y.png", (req, res) => {
    const [world, dimension, z, x, y] = req.originalUrl.split('.png')[0].split('/').slice(2);
    const tilePath = path.join(__dirname, 'tiles', world, dimension, z, `${x}/${y}.png`);

    fs.stat(tilePath, (err, stats) => {
        if (err) return res.sendStatus(404);
        res.status(200).send(stats.mtimeMs.toString());
    });
});

app.get("/download-coordinates-log", (req, res) => {
    const { world, dimension } = req.query;

    try {
        const filePath = path.join(__dirname, 'worlds', world, `${dimension}.txt`);
        if (!fs.existsSync(filePath)) return res.status(404).send('File not found');

        res.download(filePath);
    } catch (err) {
        res.status(500).send(err.message);
    }
});

app.listen(port, () => {
    console.log(`app listening at http://localhost:${port}`);
});
