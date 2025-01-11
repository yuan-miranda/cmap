const express = require('express');
const path = require('path');
const app = express();
const port = 3000;

app.use(express.static(path.join(__dirname, 'static')));
app.use("/node_modules", express.static(path.join(__dirname, 'node_modules')));
app.use("/tiles", express.static(path.join(__dirname, 'tiles')));

app.get('/', (req, res) => {
    res.sendFile("static/html/index.html", { root: __dirname });
});

app.listen(port, () => {
    console.log(`app listening at http://localhost:${port}`);
});
