import { useState } from "react";
import { encodeMessage } from "../api";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faLock,
  faRocket,
  faSpinner,
  faCheckCircle,
  faTimesCircle,
  faCopy,
  faDownload,
  faShieldAlt,
} from "@fortawesome/free-solid-svg-icons";

function EncodeTab() {
  const [coverImage, setCoverImage] = useState(null);
  const [message, setMessage] = useState("");
  const [useEncryption, setUseEncryption] = useState(false);
  const [publicKey, setPublicKey] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [coverPreview, setCoverPreview] = useState(null);

  const handleCoverImageChange = (e) => {
    const file = e.target.files[0];
    if (file && file.size > 5 * 1024 * 1024) {
      setError("Kích thước ảnh phải nhỏ hơn 5MB");
      return;
    }
    setCoverImage(file);
    setError(null);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setCoverPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handlePublicKeyChange = (e) => {
    setPublicKey(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await encodeMessage(
        coverImage,
        message,
        useEncryption,
        publicKey,
        true
      );
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result.stego_url);
    alert("Đã sao chép URL vào bộ nhớ tạm!");
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <FontAwesomeIcon icon={faLock} className="text-primary-600" />
        Mã Hóa - Ẩn Tin Nhắn Trong Ảnh
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Cover Image */}
        <div className="card">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Ảnh Gốc <span className="text-red-500">*</span>
            <span className="text-xs font-normal text-gray-500 ml-2">
              (Tối đa 5MB)
            </span>
          </label>
          <input
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleCoverImageChange}
            required
            className="input-field file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
          />
          {coverPreview && (
            <div className="mt-4 text-center">
              <img
                src={coverPreview}
                alt="Cover preview"
                className="max-w-full max-h-80 rounded-lg shadow-md mx-auto border-2 border-gray-200"
              />
            </div>
          )}
        </div>

        {/* Secret Message */}
        <div className="card">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Tin Nhắn Bí Mật <span className="text-red-500">*</span>
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Nhập tin nhắn bí mật của bạn ở đây..."
            required
            rows="6"
            className="input-field resize-none"
          />
          <p className="text-xs text-gray-500 mt-2">
            {message.length} ký tự
          </p>
        </div>

        {/* Encryption Option */}
        <div className="card bg-primary-50 border-primary-200">
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={useEncryption}
              onChange={(e) => setUseEncryption(e.target.checked)}
              className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="ml-3 text-sm font-semibold text-gray-800 flex items-center gap-2">
              <FontAwesomeIcon icon={faShieldAlt} />
              Sử Dụng Mã Hóa RSA+AES
            </span>
          </label>
          <p className="text-xs text-gray-600 mt-2 ml-8">
            Bật mã hóa để tăng cường bảo mật
          </p>
        </div>

        {/* Public Key */}
        {useEncryption && (
          <div className="card animate-fadeIn">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Khóa Công Khai (file .pem) <span className="text-red-500">*</span>
            </label>
            <input
              type="file"
              accept=".pem"
              onChange={handlePublicKeyChange}
              required={useEncryption}
              className="input-field file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className="btn-primary w-full text-lg"
          disabled={loading}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faSpinner} spin />
              Đang mã hóa...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faRocket} />
              Mã Hóa Tin Nhắn
            </span>
          )}
        </button>
      </form>

      {/* Loading State */}
      {loading && (
        <div className="mt-8 text-center py-12 bg-primary-50 rounded-xl border-2 border-primary-200">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-primary-700 font-semibold text-lg">
            Đang xử lý ảnh...
          </p>
          <p className="text-gray-600 text-sm mt-2">
            Quá trình này có thể mất vài phút
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg">
          <div className="flex items-start">
            <FontAwesomeIcon
              icon={faTimesCircle}
              className="text-2xl text-red-500 mr-3"
            />
            <div>
              <strong className="text-red-800 font-semibold">Lỗi:</strong>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && (
        <div className="mt-8 card bg-green-50 border-green-200 border-2">
          <h3 className="text-2xl font-bold text-green-800 mb-4 flex items-center gap-2">
            <FontAwesomeIcon icon={faCheckCircle} />
            Tạo Ảnh Stego Thành Công!
          </h3>

          <div className="flex flex-col md:flex-row gap-3 mb-4">
            <input
              type="text"
              value={result.stego_url}
              readOnly
              className="flex-1 px-4 py-3 bg-white border-2 border-green-300 rounded-lg font-mono text-sm"
            />
            <button
              onClick={copyToClipboard}
              className="btn-secondary whitespace-nowrap"
            >
              <FontAwesomeIcon icon={faCopy} className="mr-2" />
              Sao Chép URL
            </button>
            <a
              href={result.stego_url}
              download
              className="btn-primary whitespace-nowrap text-center"
            >
              <FontAwesomeIcon icon={faDownload} className="mr-2" />
              Tải Xuống
            </a>
          </div>

          <div className="text-center bg-white p-4 rounded-lg">
            <img
              src={result.stego_url}
              alt="Stego image"
              className="max-w-full max-h-96 rounded-lg shadow-lg mx-auto border-2 border-gray-200"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default EncodeTab;
