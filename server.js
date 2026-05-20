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
      console.error('No file uploaded');
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const jsonFile = req.files.file;
    const keysStr = req.body.keys || '';
    const type = req.body.type;

    console.log('Processing request - Keys:', keysStr, 'Type:', type);

    if (!['encrypt', 'decrypt'].includes(type)) {
      console.error('Invalid type:', type);
      return res.status(400).json({ error: 'Type must be either encrypt or decrypt' });
    }

    if (!keysStr.trim()) {
      console.error('No keys specified');
      return res.status(400).json({ error: 'Please provide at least one field name to process' });
    }

    const keys = keysStr.split(',').map(k => k.trim()).filter(Boolean);
    console.log('Parsed keys:', keys);

    const data = JSON.parse(jsonFile.data.toString('utf8'));
    console.log('File parsed successfully, starting processing...');

    const processed = encryptor.processKeys(data, keys, type);

    res.setHeader('Content-Disposition', 'attachment; filename="processed.json"');
    res.setHeader('Content-Type', 'application/json');
    return res.send(JSON.stringify(processed, null, 2));
  } catch (err) {
    console.error('Error:', err.message);
    console.error('Stack:', err.stack);
    return res.status(500).json({ error: 'Error processing file: ' + err.message });
  }
});

const PORT = process.env.PORT || 3001;;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
