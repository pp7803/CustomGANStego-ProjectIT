import { useState } from "react";
import { reverseImage } from "../api";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faRotateLeft,
  faSpinner,
  faCheckCircle,
  faTimesCircle,
  faDownload,
} from "@fortawesome/free-solid-svg-icons";

function ReverseTab() {
  const [stegoImage, setStegoImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file && file.size > 5 * 1024 * 1024) {
      setError("Kích thước ảnh phải nhỏ hơn 5MB");
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const blob = await reverseImage(stegoImage);
      const url = URL.createObjectURL(blob);
      setResult(url);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = () => {
    const a = document.createElement("a");
    a.href = result;
    a.download = "recovered.png";
    a.click();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <FontAwesomeIcon icon={faRotateLeft} className="text-primary-600" />
        Đảo Ngược - Phục Hồi Ảnh Gốc
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Ảnh Stego <span className="text-red-500">*</span>
            <span className="text-xs font-normal text-gray-500 ml-2">
              (Tối đa 5MB)
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
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">
                Xem Trước Ảnh Stego
              </h4>
              <div className="text-center">
                <img
                  src={imagePreview}
                  alt="Stego preview"
                  className="max-w-full max-h-80 rounded-lg shadow-md mx-auto border-2 border-gray-200"
                />
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          className="btn-primary w-full text-lg"
          disabled={loading}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faSpinner} spin />
              Đang phục hồi...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faRotateLeft} />
              Phục Hồi Ảnh Gốc
            </span>
          )}
        </button>
      </form>

      {loading && (
        <div className="mt-8 text-center py-12 bg-primary-50 rounded-xl border-2 border-primary-200">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-primary-700 font-semibold text-lg">
            Đang phục hồi ảnh gốc...
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
              <strong className="text-red-800 font-semibold">Lỗi:</strong>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="mt-8 card bg-green-50 border-green-200 border-2">
          <h3 className="text-2xl font-bold text-green-800 mb-4 flex items-center gap-2">
            <FontAwesomeIcon icon={faCheckCircle} />
            Phục Hồi Ảnh Thành Công!
          </h3>
          <button onClick={downloadImage} className="btn-primary mb-4">
            <FontAwesomeIcon icon={faDownload} className="mr-2" />
            Tải Xuống Ảnh Đã Phục Hồi
          </button>
          <div className="text-center bg-white p-4 rounded-lg">
            <img
              src={result}
              alt="Recovered image"
              className="max-w-full max-h-96 rounded-lg shadow-lg mx-auto border-2 border-gray-200"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default ReverseTab;
