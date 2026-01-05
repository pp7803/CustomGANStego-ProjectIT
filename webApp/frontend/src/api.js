import axios from "axios";

const API_BASE_URL = import.meta.env.PROD
  ? "https://apistegan.ppdeveloper.xyz"
  : "/api";

// const API_BASE_URL = import.meta.env.PROD ? "http://localhost:3012" : "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for large files
});

export const healthCheck = async () => {
  const response = await api.get("/health");
  return response.data;
};

export const encodeMessage = async (
  coverImage,
  message,
  useEncryption = false,
  publicKey = null,
  returnUrl = true
) => {
  const formData = new FormData();
  formData.append("cover_image", coverImage);
  formData.append("message", message);
  formData.append("return_url", returnUrl.toString());

  if (useEncryption && publicKey) {
    formData.append("use_encryption", "true");
    formData.append("public_key", publicKey);
  }

  const response = await api.post("/encode", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: returnUrl ? "json" : "blob",
  });

  return response.data;
};

export const decodeMessage = async (
  stegoImage = null,
  stegoUrl = null,
  useDecryption = false,
  privateKey = null
) => {
  const formData = new FormData();

  if (stegoImage) {
    formData.append("stego_image", stegoImage);
  } else if (stegoUrl) {
    formData.append("stego_url", stegoUrl);
  }

  if (useDecryption && privateKey) {
    formData.append("use_decryption", "true");
    formData.append("private_key", privateKey);
  }

  const response = await api.post("/decode", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
};

export const reverseImage = async (stegoImage) => {
  const formData = new FormData();
  formData.append("stego_image", stegoImage);

  const response = await api.post("/reverse", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob",
  });

  return response.data;
};

export const compareImages = async (image1, image2) => {
  const formData = new FormData();
  formData.append("image1", image1);
  formData.append("image2", image2);

  const response = await api.post("/compare", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
};

export const generateRSAKeys = async (keySize = 2048) => {
  const formData = new FormData();
  formData.append("key_size", keySize.toString());

  const response = await api.post("/genrsa", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob",
  });

  return response.data;
};

export default api;
