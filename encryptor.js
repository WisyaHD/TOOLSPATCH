const fs = require('fs');

class Encryptor {
  encryptascii(str) {
    const key = process.env.ENCRYPTION_KEY || 'b3r4sput1h';
    const dataKey = {};
    for (let i = 0; i < key.length; i++) {
      dataKey[i] = key.substr(i, 1);
    }
    let strEnc = '';
    let nkey = 0;
    const jml = str.length;
    for (let i = 0; i < parseInt(jml); i++) {
      strEnc =
        strEnc +
        this.hexEncode(str[i].charCodeAt(0) + dataKey[nkey].charCodeAt(0));
      if (nkey === Object.keys(dataKey).length - 1) {
        nkey = 0;
      }
      nkey = nkey + 1;
    }
    return strEnc.toUpperCase();
  }

  decryptascii(str) {
    if (str) {
      const key = process.env.ENCRYPTION_KEY || 'b3r4sput1h';
      const dataKey = {};
      for (let i = 0; i < key.length; i++) {
        dataKey[i] = key.substr(i, 1);
      }
      let strDec = '';
      let nkey = 0;
      const jml = str.length;
      let i = 0;
      while (i < parseInt(jml)) {
        strDec =
          strDec +
          this.chr(this.hexdec(str.substr(i, 2)) - dataKey[nkey].charCodeAt(0));
        if (nkey === Object.keys(dataKey).length - 1) {
          nkey = 0;
        }
        nkey = nkey + 1;
        i = i + 2;
      }
      return strDec;
    }
    return true;
  }

  hexEncode(str) {
    let result = '';
    result = str.toString(16);
    return result;
  }

  hexdec(hex) {
    let str = '';
    str = parseInt(hex, 16);
    return str;
  }

  chr(asci) {
    let str = '';
    str = String.fromCharCode(asci);
    return str;
  }

  processKeys(data, keys, type) {
    if (!data) return data;
    if (typeof data === 'object' && !(data instanceof Date)) {
      const result = Array.isArray(data) ? [...data] : { ...data };
      for (let key in result) {
        if (keys.includes(key)) {
          if (typeof result[key] === 'string') {
            result[key] =
              type === 'encrypt'
                ? this.encryptascii(result[key])
                : this.decryptascii(result[key]);
          } else if (typeof result[key] === 'object') {
            result[key] = this.processKeys(result[key], keys, type);
          }
        } else if (typeof result[key] === 'object') {
          result[key] = this.processKeys(result[key], keys, type);
        }
      }
      return result;
    }
    return data;
  }
}

module.exports = { Encryptor };
