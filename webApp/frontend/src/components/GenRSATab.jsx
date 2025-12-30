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
        Tạo Cặp Khóa RSA
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Kích Thước Khóa (bits)
          </label>
          <select
            value={keySize}
            onChange={(e) => setKeySize(parseInt(e.target.value))}
            className="input-field"
          >
            <option value={1024}>1024 bits (Nhanh, ít bảo mật hơn)</option>
            <option value={2048}>2048 bits (Khuyên dùng)</option>
            <option value={3072}>3072 bits (Bảo mật hơn)</option>
            <option value={4096}>4096 bits (Bảo mật tối đa)</option>
          </select>
        </div>

        <div className="card bg-yellow-50 border-yellow-300 border-2">
          <h4 className="text-lg font-bold text-yellow-900 mb-3 flex items-center gap-2">
            <FontAwesomeIcon icon={faExclamationTriangle} />
            Hướng Dẫn Bảo Mật
          </h4>
          <ul className="space-y-2 text-sm text-yellow-900">
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faCheck} className="text-green-600 mt-1" />
              <span>
                <strong>Khóa Công Khai:</strong> Chia sẻ với người gửi (để
                mã hóa)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faTimes} className="text-red-600 mt-1" />
              <span>
                <strong>Khóa Bí Mật:</strong> Giữ BÍ MẬT (để giải mã)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faTimes} className="text-red-600 mt-1" />
              <span>Không bao giờ chia sẻ hoặc tải khóa bí mật lên mạng</span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon icon={faCheck} className="text-green-600 mt-1" />
              <span>Lưu trữ khóa bí mật ở nơi an toàn</span>
            </li>
            <li className="flex items-start gap-2">
              <FontAwesomeIcon
                icon={faInfoCircle}
                className="text-blue-600 mt-1"
              />
              <span>2048 bits được khuyên dùng cho hầu hết trường hợp</span>
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
              Đang tạo khóa {keySize}-bit...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <FontAwesomeIcon icon={faShield} />
              Tạo Khóa RSA
            </span>
          )}
        </button>
      </form>

      {loading && (
        <div className="mt-8 text-center py-12 bg-primary-50 rounded-xl border-2 border-primary-200">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-primary-700 font-semibold text-lg">
            Đang tạo cặp khóa RSA {keySize}-bit...
          </p>
          <p className="text-gray-600 text-sm mt-2">
            Quá trình này có thể mất vài giây với khóa kích thước lớn
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

      {success && (
        <div className="mt-6 card bg-green-50 border-green-200 border-2">
          <strong className="text-green-800 text-lg flex items-center gap-2">
            <FontAwesomeIcon icon={faCheckCircle} />
            Thành Công!
          </strong>
          <p className="text-green-700 mt-2">
            Cặp khóa RSA đã được tạo và tải xuống.
          </p>
          <div className="mt-4 bg-white p-4 rounded-lg border border-green-200">
            <p className="font-semibold text-gray-700 mb-2">
              File ZIP chứa:
            </p>
            <ul className="space-y-1 text-sm text-gray-700">
              <li className="flex items-center gap-2">
                <FontAwesomeIcon icon={faFileAlt} className="text-green-600" />
                <code>public_key.pem</code> - để mã hóa
              </li>
              <li className="flex items-center gap-2">
                <FontAwesomeIcon icon={faFileAlt} className="text-red-600" />
                <code>private_key.pem</code> - để giải mã (giữ bí mật!)
              </li>
              <li className="flex items-center gap-2">
                <FontAwesomeIcon icon={faFileAlt} className="text-blue-600" />
                <code>README.txt</code> - hướng dẫn sử dụng
              </li>
            </ul>
          </div>
        </div>
      )}

      <div className="mt-8 space-y-6">
        <div className="card">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <FontAwesomeIcon icon={faBook} />
            Cách Sử Dụng Khóa Đã Tạo
          </h3>

          <div className="space-y-6">
            <div className="bg-primary-50 p-4 rounded-lg border-2 border-primary-200">
              <h4 className="font-bold text-primary-800 mb-3 flex items-center gap-2">
                <FontAwesomeIcon icon={faLock} />
                Để Mã Hóa (Ẩn Tin Nhắn):
              </h4>
              <ol className="list-decimal ml-6 space-y-2 text-sm text-gray-700">
                <li>
                  Đi tới tab <strong>Mã Hóa</strong>
                </li>
                <li>Chọn "Sử Dụng Mã Hóa RSA+AES"</li>
                <li>
                  Tải lên file{" "}
                  <code className="bg-white px-2 py-1 rounded">
                    public_key.pem
                  </code>{" "}
                </li>
                <li>Tin nhắn của bạn sẽ được mã hóa trước khi ẩn</li>
              </ol>
            </div>

            <div className="bg-secondary-50 p-4 rounded-lg border-2 border-secondary-200">
              <h4 className="font-bold text-secondary-800 mb-3 flex items-center gap-2">
                <FontAwesomeIcon icon={faLockOpen} />
                Để Giải Mã (Trích Xuất Tin Nhắn):
              </h4>
              <ol className="list-decimal ml-6 space-y-2 text-sm text-gray-700">
                <li>
                  Đi tới tab <strong>Giải Mã</strong>
                </li>
                <li>Chọn "Sử Dụng Giải Mã RSA+AES"</li>
                <li>
                  Tải lên file{" "}
                  <code className="bg-white px-2 py-1 rounded">
                    private_key.pem
                  </code>{" "}
                </li>
                <li>Tin nhắn đã mã hóa sẽ được giải mã tự động</li>
              </ol>
            </div>

            <div className="bg-red-50 p-4 rounded-lg border-2 border-red-200">
              <strong className="text-red-800 flex items-center gap-2">
                <FontAwesomeIcon icon={faExclamationTriangle} />
                Quan Trọng:
              </strong>
              <p className="text-red-700 mt-2 text-sm">
                Cả người gửi và người nhận đều phải có cặp khóa. Người gửi sử dụng
                khóa công khai để mã hóa, và người nhận sử dụng khóa bí mật
                để giải mã.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GenRSATab;
