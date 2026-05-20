const multipart = require('parse-multipart-data');
const { Encryptor } = require('../../encryptor');

const encryptor = new Encryptor();

exports.handler = async (event, context) => {
  // Only allow POST
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: 'Method Not Allowed'
    };
  }

  try {
    // Parse the multipart form data
    const boundary = multipart.getBoundary(event.headers['content-type']);
    const parts = multipart.parse(Buffer.from(event.body, 'base64'), boundary);

    // Find the file and form fields
    let fileData = null;
    let keys = '';
    let type = '';

    for (const part of parts) {
      if (part.name === 'file') {
        fileData = part.data;
      } else if (part.name === 'keys') {
        keys = part.data.toString('utf8');
      } else if (part.name === 'type') {
        type = part.data.toString('utf8');
      }
    }

    // Validate inputs
    if (!fileData) {
      return {
        statusCode: 400,
        body: 'No file uploaded'
      };
    }

    if (!['encrypt', 'decrypt'].includes(type)) {
      return {
        statusCode: 400,
        body: 'Type must be either encrypt or decrypt'
      };
    }

    // Process the data
    const keyArray = keys.split(',').map(k => k.trim()).filter(Boolean);
    const data = JSON.parse(fileData.toString('utf8'));
    const processed = encryptor.processKeys(data, keyArray, type);

    // Return the processed JSON
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename="processed.json"'
      },
      body: JSON.stringify(processed, null, 2)
    };

  } catch (err) {
    console.error('Error:', err);
    return {
      statusCode: 500,
      body: 'Error processing file: ' + err.message
    };
  }
};
