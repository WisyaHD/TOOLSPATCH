const express = require('express');
const fileUpload = require('express-fileupload');
const fs = require('fs');
const path = require('path');
const { Encryptor } = require('./encryptor');

const app = express();
const encryptor = new Encryptor();

app.use(fileUpload());
app.use(express.static(path.join(__dirname, 'public')));

app.post('/process', (req, res) => {
  try {
    if (!req.files || !req.files.file) {
      return res.status(400).send('No file uploaded');
    }

    const jsonFile = req.files.file;
    const keysStr = req.body.keys || '';
    const type = req.body.type;

    if (!['encrypt', 'decrypt'].includes(type)) {
      return res.status(400).send('Type must be either encrypt or decrypt');
    }

    const keys = keysStr.split(',').map(k => k.trim()).filter(Boolean);
    const data = JSON.parse(jsonFile.data.toString('utf8'));
    const processed = encryptor.processKeys(data, keys, type);

    res.setHeader('Content-Disposition', 'attachment; filename="processed.json"');
    res.setHeader('Content-Type', 'application/json');
    return res.send(JSON.stringify(processed, null, 2));
  } catch (err) {
    console.error(err);
    return res.status(500).send('Error processing file: ' + err.message);
  }
});

const PORT = process.env.PORT || 3001;;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
