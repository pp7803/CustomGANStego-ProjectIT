"""
Flask API for CustomGANStego
Web service endpoints for steganography operations
"""

import os
import io
import uuid
import zipfile
import shutil
import requests
import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, request, jsonify, send_file, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stegan_api.log')
    ]
)
logger = logging.getLogger(__name__)

# Import steganography modules
try:
    from enhancedstegan import encode_message, decode_message, reverse_hiding
    logger.info("✓ Successfully imported steganography modules")
except Exception as e:
    logger.error(f"✗ Failed to import steganography modules: {e}")
    logger.error(traceback.format_exc())
    raise

# RSA imports
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
KEYS_FOLDER = 'keys'
MODEL_FOLDER = 'model'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB for multiple file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Find best model file
BEST_MODEL_PATH = None
try:
    if os.path.exists(MODEL_FOLDER):
        # First try to find model.dat
        default_model = os.path.join(MODEL_FOLDER, 'model.dat')
        if os.path.exists(default_model):
            BEST_MODEL_PATH = default_model
            logger.info(f"✓ Found default model: {BEST_MODEL_PATH}")
        else:
            # If not found, get any .dat file (sorted by name, ep016 should be last)
            model_files = sorted([f for f in os.listdir(MODEL_FOLDER) if f.endswith('.dat')], reverse=True)
            if model_files:
                BEST_MODEL_PATH = os.path.join(MODEL_FOLDER, model_files[0])
                logger.info(f"✓ Found model: {BEST_MODEL_PATH}")
            else:
                logger.warning("⚠ No model files found, using random weights")
    else:
        logger.warning("⚠ Model folder not found, using random weights")
except Exception as e:
    logger.error(f"✗ Error loading model: {e}")

# Ensure folders exist
# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(KEYS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['KEYS_FOLDER'] = KEYS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(folder, max_age_hours=24):
    """Remove files older than max_age_hours"""
    try:
        now = datetime.now().timestamp()
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    os.remove(filepath)
    except Exception as e:
        print(f"Cleanup error: {e}")


def download_image_from_url(url, save_path):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Verify it's an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f"URL does not point to an image: {content_type}")
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        raise Exception(f"Failed to download image from URL: {str(e)}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    import sys
    import torch
    
    health_status = {
        'status': 'healthy',
        'service': 'CustomGANStego API',
        'crypto_available': CRYPTO_AVAILABLE,
        'python_version': sys.version,
        'torch_version': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'mps_available': torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False,
    }
    
    # Check if modules can be imported
    try:
        from enhancedstegan import encode_message, decode_message, reverse_hiding
        health_status['stegan_module'] = 'OK'
    except Exception as e:
        health_status['stegan_module'] = f'ERROR: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Check folders
    health_status['folders'] = {
        'uploads': os.path.exists(app.config['UPLOAD_FOLDER']),
        'outputs': os.path.exists(app.config['OUTPUT_FOLDER']),
        'keys': os.path.exists(app.config['KEYS_FOLDER']),
    }
    
    return jsonify(health_status)


@app.route('/encode', methods=['POST'])
def encode():
    """
    Encode endpoint - Hide message in image
    
    Form data:
    - cover_image: image file
    - message: text to hide
    - use_encryption: boolean (optional)
    - public_key: public key file (if use_encryption=true)
    - return_url: boolean (optional, default=true) - return URL instead of file
    """
    cover_path = None
    stego_path = None
    
    try:
        # Validate inputs
        if 'cover_image' not in request.files:
            return jsonify({'error': 'No cover image provided'}), 400
        
        if 'message' not in request.form:
            return jsonify({'error': 'No message provided'}), 400
        
        cover_file = request.files['cover_image']
        message = request.form['message']
        use_encryption = request.form.get('use_encryption', 'false').lower() == 'true'
        return_url = request.form.get('return_url', 'true').lower() == 'true'
        
        if cover_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        if not allowed_file(cover_file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, or JPEG'}), 400
        
        # Save cover image
        unique_id = str(uuid.uuid4())
        cover_filename = f"{unique_id}_cover.png"
        cover_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_filename)
        cover_file.save(cover_path)
        
        # Check file size
        cover_size = os.path.getsize(cover_path)
        if cover_size > MAX_FILE_SIZE:
            os.remove(cover_path)
            return jsonify({'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'}), 400
        
        logger.info(f"[ENCODE] Request ID: {unique_id}")
        logger.info(f"[ENCODE] Saved cover image: {cover_path}")
        
        # Handle encryption
        final_message = message
        if use_encryption:
            if 'public_key' not in request.files:
                return jsonify({'error': 'Public key required for encryption'}), 400
            
            if not CRYPTO_AVAILABLE:
                return jsonify({'error': 'Crypto library not available'}), 500
            
            pub_key_file = request.files['public_key']
            pub_key_content = pub_key_file.read().decode('utf-8')
            public_key = RSA.import_key(pub_key_content)
            
            logger.info(f"[ENCODE] Encrypting message...")
            
            # Encrypt the message using RSA+AES hybrid encryption
            # Generate AES key
            aes_key = get_random_bytes(32)  # 256-bit AES key
            
            # Encrypt message with AES
            cipher_aes = AES.new(aes_key, AES.MODE_CBC)
            iv = cipher_aes.iv
            encrypted_data = cipher_aes.encrypt(pad(message.encode('utf-8'), AES.block_size))
            
            # Encrypt AES key with RSA
            cipher_rsa = PKCS1_OAEP.new(public_key)
            encrypted_key = cipher_rsa.encrypt(aes_key)
            
            # Combine: encrypted_key_length(4 bytes) + encrypted_key + iv(16 bytes) + encrypted_data
            import struct
            key_len = struct.pack('>I', len(encrypted_key))
            encrypted_package = key_len + encrypted_key + iv + encrypted_data
            
            # Convert to base64 for text encoding
            import base64
            final_message = base64.b64encode(encrypted_package).decode('ascii')
        
        # Encode message
        stego_filename = f"{unique_id}_stego.png"
        stego_path = os.path.join(app.config['OUTPUT_FOLDER'], stego_filename)
        
        logger.info(f"[ENCODE] Starting steganography encoding...")
        logger.info(f"[ENCODE] Message length: {len(final_message)} chars")
        logger.info(f"[ENCODE] Using model: {BEST_MODEL_PATH or 'random weights'}")
        
        try:
            encode_message(
                cover_image_path=cover_path,
                secret_text=final_message,
                output_path=stego_path,
                model_path=BEST_MODEL_PATH
            )
            logger.info(f"[ENCODE] Encoding complete: {stego_path}")
        except Exception as encode_error:
            logger.error(f"[ENCODE] encode_message() failed: {encode_error}")
            logger.error(traceback.format_exc())
            raise
        
        # Cleanup
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        cleanup_old_files(app.config['OUTPUT_FOLDER'])
        
        # Return URL or file
        if return_url:
            # Build absolute URL
            base_url = request.url_root.rstrip('/')
            file_url = f"{base_url}/files/{stego_filename}"
            
            logger.info(f"[ENCODE] Success! URL: {file_url}")
            
            return jsonify({
                'success': True,
                'stego_url': file_url,
                'filename': stego_filename
            })
        else:
            return send_file(
                stego_path,
                mimetype='image/png',
                as_attachment=True,
                download_name='stego.png'
            )
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        logger.error(f"[ENCODE ERROR] {error_msg}")
        logger.error(f"[ENCODE TRACEBACK]\n{traceback_str}")
        
        # Cleanup on error
        try:
            if cover_path and os.path.exists(cover_path):
                os.remove(cover_path)
            if stego_path and os.path.exists(stego_path):
                os.remove(stego_path)
        except:
            pass
        
        return jsonify({'error': error_msg, 'traceback': traceback_str}), 500


@app.route('/decode', methods=['POST'])
def decode():
    """
    Decode endpoint - Extract message from stego image
    
    Form data:
    - stego_image: stego image file (optional if stego_url provided)
    - stego_url: URL to stego image (optional if stego_image provided)
    - use_decryption: boolean (optional)
    - private_key: private key file (if use_decryption=true)
    """
    stego_path = None
    
    try:
        unique_id = str(uuid.uuid4())
        logger.info(f"[DECODE] Request ID: {unique_id}")
        
        # Check if URL is provided
        stego_url = request.form.get('stego_url', '').strip()
        
        if stego_url:
            # Download from URL
            stego_filename = f"{unique_id}_stego_from_url.png"
            stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_filename)
            
            try:
                download_image_from_url(stego_url, stego_path)
                
                # Check file size
                stego_size = os.path.getsize(stego_path)
                if stego_size > MAX_FILE_SIZE:
                    os.remove(stego_path)
                    return jsonify({'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'}), 400
            except Exception as e:
                return jsonify({'error': f'Failed to download image from URL: {str(e)}'}), 400
        
        elif 'stego_image' in request.files:
            # Upload file
            stego_file = request.files['stego_image']
            
            if stego_file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            
            if not allowed_file(stego_file.filename):
                return jsonify({'error': 'Invalid file type. Use PNG, JPG, or JPEG'}), 400
            
            stego_filename = f"{unique_id}_stego.png"
            stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_filename)
            stego_file.save(stego_path)
            
            # Check file size
            stego_size = os.path.getsize(stego_path)
            if stego_size > MAX_FILE_SIZE:
                os.remove(stego_path)
                return jsonify({'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'}), 400
        
        else:
            return jsonify({'error': 'No stego image or URL provided'}), 400
        
        use_decryption = request.form.get('use_decryption', 'false').lower() == 'true'
        
        # Decode message
        logger.info(f"[DECODE] Using model: {BEST_MODEL_PATH or 'random weights'}")
        decoded_message = decode_message(stego_image_path=stego_path, model_path=BEST_MODEL_PATH)
        logger.info(f"[DECODE] Decoded message length: {len(decoded_message)} chars")
        
        # Handle decryption
        final_message = decoded_message
        if use_decryption:
            if 'private_key' not in request.files:
                return jsonify({'error': 'Private key required for decryption'}), 400
            
            if not CRYPTO_AVAILABLE:
                return jsonify({'error': 'Crypto library not available'}), 500
            
            priv_key_file = request.files['private_key']
            priv_key_content = priv_key_file.read().decode('utf-8')
            private_key = RSA.import_key(priv_key_content)
            
            # Decrypt the message using RSA+AES hybrid decryption
            import base64
            import struct
            
            # Decode from base64
            encrypted_package = base64.b64decode(decoded_message)
            
            # Extract components
            key_len = struct.unpack('>I', encrypted_package[:4])[0]
            encrypted_key = encrypted_package[4:4+key_len]
            iv = encrypted_package[4+key_len:4+key_len+16]
            encrypted_data = encrypted_package[4+key_len+16:]
            
            # Decrypt AES key with RSA
            cipher_rsa = PKCS1_OAEP.new(private_key)
            aes_key = cipher_rsa.decrypt(encrypted_key)
            
            # Decrypt message with AES
            cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher_aes.decrypt(encrypted_data), AES.block_size)
            final_message = decrypted_data.decode('utf-8')
        
        # Cleanup
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        
        logger.info(f"[DECODE] Success! Message length: {len(final_message)} chars")
        
        return jsonify({
            'success': True,
            'message': final_message
        })
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        logger.error(f"[DECODE ERROR] {error_msg}")
        logger.error(f"[DECODE TRACEBACK]\n{traceback_str}")
        
        # Cleanup on error
        try:
            if stego_path and os.path.exists(stego_path):
                os.remove(stego_path)
        except:
            pass
        
        return jsonify({'error': error_msg, 'traceback': traceback_str}), 500


@app.route('/reverse', methods=['POST'])
def reverse():
    """
    Reverse endpoint - Recover original cover image from stego
    
    Form data:
    - stego_image: stego image file
    """
    stego_path = None
    recovered_path = None
    
    try:
        logger.info("[REVERSE] Starting reverse operation...")
        if 'stego_image' not in request.files:
            return jsonify({'error': 'No stego image provided'}), 400
        
        stego_file = request.files['stego_image']
        
        if stego_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        if not allowed_file(stego_file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, or JPEG'}), 400
        
        # Save stego image
        unique_id = str(uuid.uuid4())
        stego_filename = f"{unique_id}_stego.png"
        stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_filename)
        stego_file.save(stego_path)
        
        # Check file size
        stego_size = os.path.getsize(stego_path)
        if stego_size > MAX_FILE_SIZE:
            os.remove(stego_path)
            return jsonify({'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'}), 400
        
        # Reverse to recover cover
        recovered_filename = f"{unique_id}_recovered.png"
        recovered_path = os.path.join(app.config['OUTPUT_FOLDER'], recovered_filename)
        
        # Check if model exists and has reverse decoder weights
        if not BEST_MODEL_PATH:
            return jsonify({'error': 'No trained model available. Reverse hiding requires a trained model.'}), 500
        
        logger.info(f"[REVERSE] Using model: {BEST_MODEL_PATH}")
        
        try:
            reverse_hiding(
                stego_image_path=stego_path,
                output_path=recovered_path,
                model_path=BEST_MODEL_PATH
            )
        except ValueError as ve:
            # Handle missing reverse decoder weights
            logger.error(f"[REVERSE] Model validation failed: {ve}")
            return jsonify({'error': str(ve)}), 400
        except Exception as reverse_error:
            logger.error(f"[REVERSE] reverse_hiding() failed: {reverse_error}")
            logger.error(traceback.format_exc())
            raise
        
        # Cleanup
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        cleanup_old_files(app.config['OUTPUT_FOLDER'])
        
        logger.info(f"[REVERSE] Success! Recovered image: {recovered_path}")
        
        return send_file(
            recovered_path,
            mimetype='image/png',
            as_attachment=True,
            download_name='recovered.png'
        )
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        logger.error(f"[REVERSE ERROR] {error_msg}")
        logger.error(f"[REVERSE TRACEBACK]\n{traceback_str}")
        
        # Cleanup on error
        try:
            if stego_path and os.path.exists(stego_path):
                os.remove(stego_path)
            if recovered_path and os.path.exists(recovered_path):
                os.remove(recovered_path)
        except:
            pass
        
        return jsonify({'error': error_msg, 'traceback': traceback_str}), 500


@app.route('/compare', methods=['POST'])
def compare():
    """
    Compare endpoint - Calculate metrics between two images
    
    Form data:
    - image1: first image file
    - image2: second image file
    """
    img1_path = None
    img2_path = None
    
    try:
        logger.info("[COMPARE] Starting image comparison...")
        if 'image1' not in request.files or 'image2' not in request.files:
            return jsonify({'error': 'Both images required'}), 400
        
        img1_file = request.files['image1']
        img2_file = request.files['image2']
        
        if img1_file.filename == '' or img2_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        if not allowed_file(img1_file.filename) or not allowed_file(img2_file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, or JPEG'}), 400
        
        # Save images
        unique_id = str(uuid.uuid4())
        img1_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_img1.png")
        img2_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_img2.png")
        
        img1_file.save(img1_path)
        img2_file.save(img2_path)
        
        # Check file sizes
        img1_size = os.path.getsize(img1_path)
        img2_size = os.path.getsize(img2_path)
        if img1_size > MAX_FILE_SIZE or img2_size > MAX_FILE_SIZE:
            os.remove(img1_path)
            os.remove(img2_path)
            return jsonify({'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'}), 400
        
        # Load images
        img1 = np.array(Image.open(img1_path).convert('RGB'))
        img2 = np.array(Image.open(img2_path).convert('RGB'))
        
        # Ensure same size
        if img1.shape != img2.shape:
            # Resize img2 to match img1
            img2_pil = Image.fromarray(img2).resize((img1.shape[1], img1.shape[0]))
            img2 = np.array(img2_pil)
        
        # Calculate metrics
        psnr_value = psnr(img1, img2, data_range=255)
        ssim_value = ssim(img1, img2, channel_axis=2, data_range=255)
        mse_value = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
        
        # Cleanup
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        
        logger.info(f"[COMPARE] Success! PSNR={psnr_value:.2f}, SSIM={ssim_value:.4f}, MSE={mse_value:.2f}")
        
        return jsonify({
            'success': True,
            'metrics': {
                'psnr': float(psnr_value),
                'ssim': float(ssim_value),
                'mse': float(mse_value)
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        logger.error(f"[COMPARE ERROR] {error_msg}")
        logger.error(f"[COMPARE TRACEBACK]\n{traceback_str}")
        
        # Cleanup on error
        try:
            if img1_path and os.path.exists(img1_path):
                os.remove(img1_path)
            if img2_path and os.path.exists(img2_path):
                os.remove(img2_path)
        except:
            pass
        
        return jsonify({'error': error_msg, 'traceback': traceback_str}), 500


@app.route('/genrsa', methods=['POST'])
def genrsa():
    """
    Generate RSA key pair
    
    Form data:
    - key_size: key size in bits (1024, 2048, 3072, 4096)
    """
    keys_dir = None
    zip_path = None
    
    try:
        logger.info("[GENRSA] Starting RSA key generation...")
        if not CRYPTO_AVAILABLE:
            return jsonify({'error': 'Crypto library not available'}), 500
        
        key_size = int(request.form.get('key_size', 2048))
        
        if key_size not in [1024, 2048, 3072, 4096]:
            return jsonify({'error': 'Invalid key size. Use 1024, 2048, 3072, or 4096'}), 400
        
        # Generate RSA key pair
        key = RSA.generate(key_size)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        
        # Create unique directory for this key pair
        unique_id = str(uuid.uuid4())
        keys_dir = os.path.join(app.config['KEYS_FOLDER'], unique_id)
        os.makedirs(keys_dir, exist_ok=True)
        
        # Save keys
        private_key_path = os.path.join(keys_dir, 'private_key.pem')
        public_key_path = os.path.join(keys_dir, 'public_key.pem')
        
        with open(private_key_path, 'wb') as f:
            f.write(private_key)
        
        with open(public_key_path, 'wb') as f:
            f.write(public_key)
        
        # Create ZIP file
        zip_filename = f"rsa_keys_{key_size}bit.zip"
        zip_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{unique_id}_{zip_filename}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(private_key_path, 'private_key.pem')
            zipf.write(public_key_path, 'public_key.pem')
            
            # Add README
            readme_content = f"""RSA Key Pair - {key_size} bits
================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Files:
- private_key.pem: Private key (keep secret!)
- public_key.pem: Public key (can be shared)

Usage:
1. Use public_key.pem for encryption during encoding
2. Use private_key.pem for decryption during decoding

IMPORTANT: Keep private_key.pem secure and never share it!
"""
            zipf.writestr('README.txt', readme_content)
        
        # Cleanup keys directory
        shutil.rmtree(keys_dir)
        cleanup_old_files(app.config['KEYS_FOLDER'])
        cleanup_old_files(app.config['OUTPUT_FOLDER'])
        
        logger.info(f"[GENRSA] Success! Generated {key_size}-bit RSA keys")
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        logger.error(f"[GENRSA ERROR] {error_msg}")
        logger.error(f"[GENRSA TRACEBACK]\n{traceback_str}")
        
        # Cleanup on error
        try:
            if keys_dir and os.path.exists(keys_dir):
                shutil.rmtree(keys_dir)
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
        except:
            pass
        
        return jsonify({'error': error_msg, 'traceback': traceback_str}), 500


@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    """
    Serve output files (stego images, recovered images)
    
    Path parameter:
    - filename: name of the file to serve
    """
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        logger.info(f"[FILES] Serving file: {filename}")
        
        return send_file(
            file_path,
            mimetype='image/png'
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[FILES ERROR] {error_msg}")
        return jsonify({'error': error_msg}), 500


if __name__ == '__main__':
    try:
        logger.info("=" * 50)
        logger.info("CustomGANStego API Server")
        logger.info("=" * 50)
        logger.info("Endpoints:")
        logger.info("  POST /encode         - Hide message in image")
        logger.info("  POST /decode         - Extract message from image (file or URL)")
        logger.info("  POST /reverse        - Recover original image")
        logger.info("  POST /compare        - Compare two images")
        logger.info("  POST /genrsa         - Generate RSA key pair")
        logger.info("  GET  /files/<name>   - Serve output files")
        logger.info("  GET  /health         - Health check")
        logger.info("=" * 50)
        logger.info("")
        logger.info("Server running at: http://localhost:3012")
        logger.info("Logging to: stegan_api.log")
        logger.info("")
        
        app.run(host='0.0.0.0', port=3012, debug=True)
    
    except Exception as e:
        logger.critical("=" * 50)
        logger.critical("FATAL ERROR - Server failed to start")
        logger.critical("=" * 50)
        logger.critical(f"Error: {e}")
        logger.critical(f"Traceback:\n{traceback.format_exc()}")
        logger.critical("=" * 50)
        sys.exit(1)
