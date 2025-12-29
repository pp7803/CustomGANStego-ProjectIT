import { useState } from "react";
import { decodeMessage } from "../api";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faLockOpen,
  faSearch,
  faSpinner,
  faCheckCircle,
  faTimesCircle,
  faFile,
  faLink,
  faShieldAlt,
} from "@fortawesome/free-solid-svg-icons";

function DecodeTab() {
  const [inputMethod, setInputMethod] = useState("file"); // 'file' or 'url'
  const [stegoImage, setStegoImage] = useState(null);
  const [stegoUrl, setStegoUrl] = useState("");
  const [useDecryption, setUseDecryption] = useState(false);
  const [privateKey, setPrivateKey] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file && file.size > 5 * 1024 * 1024) {
      setError("Image size must be less than 5MB");
      return;
    }
    setStegoImage(file);
    setError(null);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handlePrivateKeyChange = (e) => {
    setPrivateKey(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await decodeMessage(
        inputMethod === "file" ? stegoImage : null,
        inputMethod === "url" ? stegoUrl : null,
        useDecryption,
        privateKey
      );
      setResult(data.message);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <FontAwesomeIcon icon={faLockOpen} className="text-primary-600" />
        Decode - Extract Hidden Message
      </h2>

      <div className="card mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          Input Method
        </label>
        <div className="flex gap-6">
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              name="method"
              checked={inputMethod === "file"}
              onChange={() => setInputMethod("file")}
              className="w-5 h-5 text-primary-600 border-gray-300 focus:ring-primary-500"
            />
            <span className="ml-2 text-sm font-medium text-gray-700">
              <FontAwesomeIcon icon={faFile} className="mr-2" />
              Upload File
            </span>
          </label>
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              name="method"
              checked={inputMethod === "url"}
              onChange={() => setInputMethod("url")}
              className="w-5 h-5 text-primary-600 border-gray-300 focus:ring-primary-500"
            />
            <span className="ml-2 text-sm font-medium text-gray-700">
              <FontAwesomeIcon icon={faLink} className="mr-2" />
              Use URL
            </span>
          </label>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {inputMethod === "file" ? (
          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Stego Image <span className="text-red-500">*</span>
              <span className="text-xs font-normal text-gray-500 ml-2">
                (Max 5MB)
              </span>
            </label>
            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              onChange={handleImageChange}
              required
              className="input-field file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
            {imagePreview && (
              <div className="mt-4 text-center">
                <img
                  src={imagePreview}
                  alt="Stego preview"
                  className="max-w-full max-h-80 rounded-lg shadow-md mx-auto border-2 border-gray-200"
                />
              </div>
            )}
          </div>
        ) : (
          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Stego Image URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              value={stegoUrl}
              onChange={(e) => setStegoUrl(e.target.value)}
              placeholder="https://example.com/stego.png"
              required
              className="input-field"
            />
          </div>
        )}

        <div className="card bg-primary-50 border-primary-200">
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={useDecryption}
              onChange={(e) => setUseDecryption(e.target.checked)}
              className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="ml-3 text-sm font-semibold text-gray-800 flex items-center gap-2">
              <FontAwesomeIcon icon={faShieldAlt} />
              Use RSA+AES Decryption
            </span>
          </label>
        </div>

        {useDecryption && (
          <div className="card animate-fadeIn">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Private Key (.pem file) <span className="text-red-500">*</span>
            </label>
            <input
              type="file"
              accept=".pem"
              onChange={handlePrivateKeyChange}
              required={useDecryption}
              className="input-field file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
          </div>
        )}

        <button
          type="submit"
          className="btn-primary w-full text-lg"
          disabled={loading}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faSpinner} spin />
              Decoding...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faSearch} />
              Decode Message
            </span>
          )}
        </button>
      </form>

      {loading && (
        <div className="mt-8 text-center py-12 bg-primary-50 rounded-xl border-2 border-primary-200">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-primary-700 font-semibold text-lg">
            Extracting message...
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

      {result && (
        <div className="mt-8 card bg-green-50 border-green-200 border-2">
          <h3 className="text-2xl font-bold text-green-800 mb-4 flex items-center gap-2">
            <FontAwesomeIcon icon={faCheckCircle} />
            Decoded Message
          </h3>
          <div className="bg-white p-6 rounded-lg border-2 border-green-300 whitespace-pre-wrap break-words font-mono text-sm">
            {result}
          </div>
        </div>
      )}
    </div>
  );
}

export default DecodeTab;
