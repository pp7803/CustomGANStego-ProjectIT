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

# Import steganography modules
from enhancedstegan import encode_message, decode_message, reverse_hiding

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
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(KEYS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['KEYS_FOLDER'] = KEYS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


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
    return jsonify({
        'status': 'healthy',
        'service': 'CustomGANStego API',
        'crypto_available': CRYPTO_AVAILABLE
    })


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
        
        # Handle encryption
        public_key = None
        if use_encryption:
            if 'public_key' not in request.files:
                return jsonify({'error': 'Public key required for encryption'}), 400
            
            if not CRYPTO_AVAILABLE:
                return jsonify({'error': 'Crypto library not available'}), 500
            
            pub_key_file = request.files['public_key']
            pub_key_content = pub_key_file.read().decode('utf-8')
            public_key = RSA.import_key(pub_key_content)
        
        # Encode message
        stego_filename = f"{unique_id}_stego.png"
        stego_path = os.path.join(app.config['OUTPUT_FOLDER'], stego_filename)
        
        encode_message(
            cover_image_path=cover_path,
            secret_text=message,
            output_path=stego_path,
            public_key=public_key
        )
        
        # Cleanup
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        cleanup_old_files(app.config['OUTPUT_FOLDER'])
        
        # Return URL or file
        if return_url:
            # Build absolute URL
            base_url = request.url_root.rstrip('/')
            file_url = f"{base_url}/files/{stego_filename}"
            
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
        return jsonify({'error': str(e)}), 500


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
    try:
        stego_path = None
        unique_id = str(uuid.uuid4())
        
        # Check if URL is provided
        stego_url = request.form.get('stego_url', '').strip()
        
        if stego_url:
            # Download from URL
            stego_filename = f"{unique_id}_stego_from_url.png"
            stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_filename)
            
            try:
                download_image_from_url(stego_url, stego_path)
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
        
        else:
            return jsonify({'error': 'No stego image or URL provided'}), 400
        
        use_decryption = request.form.get('use_decryption', 'false').lower() == 'true'
        
        # Handle decryption
        private_key = None
        if use_decryption:
            if 'private_key' not in request.files:
                return jsonify({'error': 'Private key required for decryption'}), 400
            
            if not CRYPTO_AVAILABLE:
                return jsonify({'error': 'Crypto library not available'}), 500
            
            priv_key_file = request.files['private_key']
            priv_key_content = priv_key_file.read().decode('utf-8')
            private_key = RSA.import_key(priv_key_content)
        
        # Decode message
        message = decode_message(
            stego_image_path=stego_path,
            private_key=private_key
        )
        
        # Cleanup
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reverse', methods=['POST'])
def reverse():
    """
    Reverse endpoint - Recover original cover image from stego
    
    Form data:
    - stego_image: stego image file
    """
    try:
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
        
        # Reverse to recover cover
        recovered_filename = f"{unique_id}_recovered.png"
        recovered_path = os.path.join(app.config['OUTPUT_FOLDER'], recovered_filename)
        
        reverse_hiding(
            stego_image_path=stego_path,
            output_path=recovered_path
        )
        
        # Cleanup
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        cleanup_old_files(app.config['OUTPUT_FOLDER'])
        
        return send_file(
            recovered_path,
            mimetype='image/png',
            as_attachment=True,
            download_name='recovered.png'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/compare', methods=['POST'])
def compare():
    """
    Compare endpoint - Calculate metrics between two images
    
    Form data:
    - image1: first image file
    - image2: second image file
    """
    try:
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
        
        return jsonify({
            'success': True,
            'metrics': {
                'psnr': float(psnr_value),
                'ssim': float(ssim_value),
                'mse': float(mse_value)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/genrsa', methods=['POST'])
def genrsa():
    """
    Generate RSA key pair
    
    Form data:
    - key_size: key size in bits (1024, 2048, 3072, 4096)
    """
    try:
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
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        
        return send_file(
            file_path,
            mimetype='image/png'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("CustomGANStego API Server")
    print("=" * 50)
    print("Endpoints:")
    print("  POST /encode         - Hide message in image")
    print("  POST /decode         - Extract message from image (file or URL)")
    print("  POST /reverse        - Recover original image")
    print("  POST /compare        - Compare two images")
    print("  POST /genrsa         - Generate RSA key pair")
    print("  GET  /files/<name>   - Serve output files")
    print("  GET  /health         - Health check")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
