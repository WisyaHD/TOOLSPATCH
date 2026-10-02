const fs = require('fs');

class Encryptor {
  encryptascii(str) {
    const key = process.env.ENCRYPTION_KEY || 'b3r4sput1h';
    const encodedCharacters = [];
    let needsWideEncoding = false;
    for (let i = 0; i < str.length; i++) {
      const encodedCharacter =
        str.charCodeAt(i) + key.charCodeAt(i % key.length);
      encodedCharacters.push(encodedCharacter);
      if (encodedCharacter < 16 || encodedCharacter > 255) {
        needsWideEncoding = true;
      }
    }

    if (needsWideEncoding) {
      return 'U1' + encodedCharacters
        .map((character) => character.toString(16).padStart(5, '0'))
        .join('')
        .toUpperCase();
    }

    return encodedCharacters
      .map((character) => this.hexEncode(character))
      .join('')
      .toUpperCase();
  }

  decryptascii(str) {
    if (str) {
      const key = process.env.ENCRYPTION_KEY || 'b3r4sput1h';
      if (str.startsWith('U1')) {
        let decoded = '';
        for (let i = 2; i < str.length; i += 5) {
          const keyCode = key.charCodeAt(((i - 2) / 5) % key.length);
          decoded += this.chr(parseInt(str.substr(i, 5), 16) - keyCode);
        }
        return decoded;
      }

      const dataKey = {};
      for (let i = 0; i < key.length; i++) {
        dataKey[i] = key.substr(i, 1);
      }
      let strDec = '';
      let moduloDecoded = '';
      let nkey = 0;
      const jml = str.length;
      let i = 0;
      while (i < parseInt(jml)) {
        const encodedCharacter = this.hexdec(str.substr(i, 2));
        strDec =
          strDec +
          this.chr(encodedCharacter - dataKey[nkey].charCodeAt(0));
        moduloDecoded += this.chr(
          encodedCharacter - key.charCodeAt((i / 2) % key.length)
        );
        if (nkey === Object.keys(dataKey).length - 1) {
          nkey = 0;
        }
        nkey = nkey + 1;
        i = i + 2;
      }
      if (/[\u0000-\u001F\u007F-\u009F\uFFFD\uFFFE\uFFFF]/.test(strDec)) {
        if (!/[\u0000-\u001F\u007F-\u009F\uFFFD\uFFFE\uFFFF]/.test(moduloDecoded)) {
          return moduloDecoded;
        }
        const recovered = this.recoverLegacyUnicode(str, key);
        if (recovered !== null) return recovered;
      }
      return strDec;
    }
    return true;
  }

  recoverLegacyUnicode(str, key) {
    if (!/^[0-9a-f]+$/i.test(str)) return null;

    const memo = new Map();
    const find = (offset, keyIndex) => {
      if (offset === str.length) return [''];
      const state = `${offset}:${keyIndex}`;
      if (memo.has(state)) return memo.get(state);

      const solutions = [];
      for (let width = 1; width <= 5 && offset + width <= str.length; width++) {
        const segment = str.slice(offset, offset + width);
        const encodedCharacter = parseInt(segment, 16);
        if (encodedCharacter.toString(16).length !== width) continue;

        const characterCode = encodedCharacter - key.charCodeAt(keyIndex);
        if (characterCode < 0 || characterCode > 0xFFFF) continue;
        if (characterCode >= 0xD800 && characterCode <= 0xDFFF) continue;
        if (!/[\p{Script=Latin}\p{N}\p{P}\p{S}\p{Z}]/u.test(String.fromCharCode(characterCode))) continue;

        for (const suffix of find(offset + width, (keyIndex + 1) % key.length)) {
          solutions.push(String.fromCharCode(characterCode) + suffix);
          if (solutions.length > 1) break;
        }
        if (solutions.length > 1) break;
      }

      memo.set(state, solutions);
      return solutions;
    };

    const solutions = find(0, 0);
    return solutions.length === 1 ? solutions[0] : null;
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
