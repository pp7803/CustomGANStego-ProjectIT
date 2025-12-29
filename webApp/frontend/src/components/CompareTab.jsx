import { useState } from "react";
import { compareImages } from "../api";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faChartBar,
  faCalculator,
  faSpinner,
  faTimesCircle,
  faBook,
} from "@fortawesome/free-solid-svg-icons";

function CompareTab() {
  const [image1, setImage1] = useState(null);
  const [image2, setImage2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [preview1, setPreview1] = useState(null);
  const [preview2, setPreview2] = useState(null);

  const handleImage1Change = (e) => {
    const file = e.target.files[0];
    if (file && file.size > 5 * 1024 * 1024) {
      setError("Image size must be less than 5MB");
      return;
    }
    setImage1(file);
    setError(null);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview1(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleImage2Change = (e) => {
    const file = e.target.files[0];
    if (file && file.size > 5 * 1024 * 1024) {
      setError("Image size must be less than 5MB");
      return;
    }
    setImage2(file);
    setError(null);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview2(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await compareImages(image1, image2);
      setResult(data.metrics);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  const getQualityBadge = (psnr, ssim) => {
    if (psnr > 40 && ssim > 0.95)
      return { text: "Excellent", color: "bg-green-500" };
    if (psnr > 30 && ssim > 0.9)
      return { text: "Good", color: "bg-yellow-500" };
    return { text: "Fair", color: "bg-red-500" };
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <FontAwesomeIcon icon={faChartBar} className="text-primary-600" />
        Compare - Calculate Image Metrics
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Image 1 (Original/Cover) <span className="text-red-500">*</span>
              <span className="text-xs font-normal text-gray-500 ml-2">
                (Max 5MB)
              </span>
            </label>
            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              onChange={handleImage1Change}
              required
              className="input-field file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
            {preview1 && (
              <div className="mt-4 text-center">
                <img
                  src={preview1}
                  alt="Image 1"
                  className="max-w-full max-h-60 rounded-lg shadow-md mx-auto border-2 border-gray-200"
                />
              </div>
            )}
          </div>

          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Image 2 (Stego/Recovered) <span className="text-red-500">*</span>
              <span className="text-xs font-normal text-gray-500 ml-2">
                (Max 5MB)
              </span>
            </label>
            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              onChange={handleImage2Change}
              required
              className="input-field file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
            {preview2 && (
              <div className="mt-4 text-center">
                <img
                  src={preview2}
                  alt="Image 2"
                  className="max-w-full max-h-60 rounded-lg shadow-md mx-auto border-2 border-gray-200"
                />
              </div>
            )}
          </div>
        </div>

        <button
          type="submit"
          className="btn-primary w-full text-lg"
          disabled={loading}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faSpinner} spin />
              Calculating...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faCalculator} />
              Calculate Metrics
            </span>
          )}
        </button>
      </form>

      {loading && (
        <div className="mt-8 text-center py-12 bg-primary-50 rounded-xl border-2 border-primary-200">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-primary-700 font-semibold text-lg">
            Comparing images...
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
        <div className="mt-8 space-y-6">
          <div className="card bg-gradient-to-r from-primary-50 to-secondary-50 border-primary-200 border-2">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">
              Image Quality Metrics
            </h3>

            <div className="grid md:grid-cols-3 gap-6 mb-6">
              <div className="bg-white rounded-xl p-6 shadow-md text-center border-2 border-primary-100">
                <div className="text-sm text-gray-600 font-semibold mb-2">
                  PSNR
                </div>
                <div className="text-4xl font-bold text-primary-600">
                  {result.psnr.toFixed(2)}
                </div>
                <div className="text-sm text-gray-500 mt-1">dB</div>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md text-center border-2 border-primary-100">
                <div className="text-sm text-gray-600 font-semibold mb-2">
                  SSIM
                </div>
                <div className="text-4xl font-bold text-primary-600">
                  {result.ssim.toFixed(4)}
                </div>
                <div className="text-sm text-gray-500 mt-1">index</div>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md text-center border-2 border-primary-100">
                <div className="text-sm text-gray-600 font-semibold mb-2">
                  MSE
                </div>
                <div className="text-4xl font-bold text-primary-600">
                  {result.mse.toFixed(2)}
                </div>
                <div className="text-sm text-gray-500 mt-1">error</div>
              </div>
            </div>

            <div
              className={`${
                getQualityBadge(result.psnr, result.ssim).color
              } text-white rounded-xl p-4 text-center`}
            >
              <div className="text-2xl font-bold">
                Quality: {getQualityBadge(result.psnr, result.ssim).text}
              </div>
            </div>
          </div>

          <div className="card">
            <h4 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <FontAwesomeIcon icon={faBook} />
              Understanding the Metrics
            </h4>
            <div className="space-y-4 text-sm text-gray-700">
              <div>
                <strong className="text-primary-600">
                  PSNR (Peak Signal-to-Noise Ratio):
                </strong>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>&gt; 40 dB: Excellent quality - virtually identical</li>
                  <li>30-40 dB: Good quality - minor differences</li>
                  <li>&lt; 30 dB: Fair quality - noticeable differences</li>
                </ul>
              </div>
              <div>
                <strong className="text-primary-600">
                  SSIM (Structural Similarity Index):
                </strong>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>&gt; 0.95: Very similar structures</li>
                  <li>0.90-0.95: Similar structures</li>
                  <li>&lt; 0.90: Moderate similarity</li>
                </ul>
              </div>
              <div>
                <strong className="text-primary-600">
                  MSE (Mean Squared Error):
                </strong>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>Lower values indicate better similarity</li>
                  <li>0 means identical images</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CompareTab;
