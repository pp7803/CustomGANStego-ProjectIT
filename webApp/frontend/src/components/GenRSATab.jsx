import { useState } from "react";
import { generateRSAKeys } from "../api";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faKey,
  faShield,
  faSpinner,
  faCheckCircle,
  faTimesCircle,
  faFileAlt,
  faLock,
  faLockOpen,
  faExclamationTriangle,
  faBook,
  faCheck,
  faTimes,
  faInfoCircle,
} from "@fortawesome/free-solid-svg-icons";

function GenRSATab() {
  const [keySize, setKeySize] = useState(2048);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const blob = await generateRSAKeys(keySize);

      // Download the ZIP file
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rsa_keys_${keySize}bit.zip`;
      a.click();
      URL.revokeObjectURL(url);

      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <FontAwesomeIcon icon={faKey} className="text-primary-600" />
        Generate RSA Key Pair
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Key Size (bits)
          </label>
          <select
            value={keySize}
            onChange={(e) => setKeySize(parseInt(e.target.value))}
            className="input-field"
          >
            <option value={1024}>1024 bits (Fast, less secure)</option>
            <option value={2048}>2048 bits (Recommended)</option>
            <option value={3072}>3072 bits (More secure)</option>
            <option value={4096}>4096 bits (Maximum security)</option>
          </select>
        </div>

        <div className="card bg-yellow-50 border-yellow-300 border-2">
          <h4 className="text-lg font-bold text-yellow-900 mb-3 flex items-center gap-2">
            <FontAwesomeIcon icon={faExclamationTriangle} />
            Security Guidelines
          </h4>
          <ul className="space-y-2 text-sm text-yellow-900">
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faCheck} className="text-green-600 mt-1" />
              <span>
                <strong>Public Key:</strong> Share this with senders (for
                encryption)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faTimes} className="text-red-600 mt-1" />
              <span>
                <strong>Private Key:</strong> Keep this SECRET (for decryption)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faTimes} className="text-red-600 mt-1" />
              <span>Never share or upload your private key online</span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faCheck} className="text-green-600 mt-1" />
              <span>Store private key in a secure location</span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon
                icon={faInfoCircle}
                className="text-blue-600 mt-1"
              />
              <span>2048 bits is recommended for most use cases</span>
            </li>
          </ul>
        </div>

        <button
          type="submit"
          className="btn-primary w-full text-lg"
          disabled={loading}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faSpinner} spin />
              Generating {keySize}-bit keys...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faShield} />
              Generate RSA Keys
            </span>
          )}
        </button>
      </form>

      {loading && (
        <div className="mt-8 text-center py-12 bg-primary-50 rounded-xl border-2 border-primary-200">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-primary-700 font-semibold text-lg">
            Generating {keySize}-bit RSA key pair...
          </p>
          <p className="text-gray-600 text-sm mt-2">
            This may take a few seconds for larger key sizes
          </p>
        </div>
      )}

      {error && (
        <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg">
          <div className="flex items-start">
            <FontAwesomeIcon
              icon={faTimesCircle}
              className="text-2xl text-red-500 mr-3"
            />
            <div>
              <strong className="text-red-800 font-semibold">Error:</strong>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mt-6 card bg-green-50 border-green-200 border-2">
          <strong className="text-green-800 text-lg flex items-center gap-2">
            <FontAwesomeIcon icon={faCheckCircle} />
            Success!
          </strong>
          <p className="text-green-700 mt-2">
            RSA key pair generated and downloaded.
          </p>
          <div className="mt-4 bg-white p-4 rounded-lg border border-green-200">
            <p className="font-semibold text-gray-700 mb-2">
              The ZIP file contains:
            </p>
            <ul className="space-y-1 text-sm text-gray-700">
              <li className="flex items-center gap-2">
                <FontAwesomeIcon icon={faFileAlt} className="text-green-600" />
                <code>public_key.pem</code> - for encryption
              </li>
              <li className="flex items-center gap-2">
                <FontAwesomeIcon icon={faFileAlt} className="text-red-600" />
                <code>private_key.pem</code> - for decryption (keep secret!)
              </li>
              <li className="flex items-center gap-2">
                <FontAwesomeIcon icon={faFileAlt} className="text-blue-600" />
                <code>README.txt</code> - usage instructions
              </li>
            </ul>
          </div>
        </div>
      )}

      <div className="mt-8 space-y-6">
        <div className="card">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <FontAwesomeIcon icon={faBook} />
            How to Use Generated Keys
          </h3>

          <div className="space-y-6">
            <div className="bg-primary-50 p-4 rounded-lg border-2 border-primary-200">
              <h4 className="font-bold text-primary-800 mb-3 flex items-center gap-2">
                <FontAwesomeIcon icon={faLock} />
                For Encoding (Hiding Messages):
              </h4>
              <ol className="list-decimal ml-6 space-y-2 text-sm text-gray-700">
                <li>
                  Go to the <strong>Encode</strong> tab
                </li>
                <li>Check "Use RSA+AES Encryption"</li>
                <li>
                  Upload the{" "}
                  <code className="bg-white px-2 py-1 rounded">
                    public_key.pem
                  </code>{" "}
                  file
                </li>
                <li>Your message will be encrypted before hiding</li>
              </ol>
            </div>

            <div className="bg-secondary-50 p-4 rounded-lg border-2 border-secondary-200">
              <h4 className="font-bold text-secondary-800 mb-3 flex items-center gap-2">
                <FontAwesomeIcon icon={faLockOpen} />
                For Decoding (Extracting Messages):
              </h4>
              <ol className="list-decimal ml-6 space-y-2 text-sm text-gray-700">
                <li>
                  Go to the <strong>Decode</strong> tab
                </li>
                <li>Check "Use RSA+AES Decryption"</li>
                <li>
                  Upload the{" "}
                  <code className="bg-white px-2 py-1 rounded">
                    private_key.pem
                  </code>{" "}
                  file
                </li>
                <li>The encrypted message will be decrypted automatically</li>
              </ol>
            </div>

            <div className="bg-red-50 p-4 rounded-lg border-2 border-red-200">
              <strong className="text-red-800 flex items-center gap-2">
                <FontAwesomeIcon icon={faExclamationTriangle} />
                Important:
              </strong>
              <p className="text-red-700 mt-2 text-sm">
                Both sender and receiver must have the key pair. The sender uses
                the public key to encrypt, and the receiver uses the private key
                to decrypt.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GenRSATab;
