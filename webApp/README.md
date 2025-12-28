# 🌐 CustomGANStego - Web Application# 🌐 CustomGANStego - Web Application# 🔐 Steganography V4 - Web Application

Web-based steganography application using Deep Learning GAN for hiding and revealing secret messages in images.Web-based steganography application using Deep Learning GAN for hiding and revealing secret messages in images.Full-stack web application for image steganography with React frontend and Express backend.

## 🏗️ Architecture## 🏗️ Architecture## 📁 Structure

````````

webApp/

├── README.md                     # This filewebApp/webApp/

├── .gitignore                    # Git ignore rules

├── BE/                           # Backend (Node.js + Express + Python)├── venv/                           # Python virtual environment (auto-created)├── prjvenv/               ← Python virtual environment (local)

│   ├── venv/                     # Python virtual environment (auto-created)

│   ├── EN_DE_ep50_*.dat         # Pre-trained model (~790KB)├── EN_DE_ep50_*.dat               # Pre-trained model (~790KB)│   ├── bin/python        ← Python interpreter

│   ├── encoder.py                # Encoder neural network

│   ├── decoder.py                # Decoder neural network  ├── encoder.py                     # Encoder neural network│   └── lib/              ← Installed packages

│   ├── critic.py                 # Critic network

│   ├── enhancedstegan.py        # Main steganography functions├── decoder.py                     # Decoder neural network  │

│   ├── genRSA.py                 # RSA key generation

│   ├── requirements.txt          # Python dependencies├── critic.py                      # Critic network├── requirements.txt       ← Python dependencies

│   ├── server.js                 # Express API server

│   ├── package.json              # Node.js dependencies├── enhancedstegan.py             # Main steganography functions│

│   └── tmp/                      # Temporary upload folder (auto-created)

└── FE/                           # Frontend (React + Vite)├── requirements.txt              # Python dependencies├── BE/                    ← Backend (Node.js + Express)

    ├── src/

    │   ├── App.jsx               # Main React app├── .gitignore                    # Git ignore rules│   ├── server.js         ← API server

    │   ├── components/

    │   │   ├── EncodeTab.jsx     # Hide message tab├── README.md                     # This file│   ├── package.json      ← Dependencies

    │   │   ├── DecodeTab.jsx     # Reveal message tab

    │   │   └── GenKeyTab.jsx     # Generate RSA keys tab├── BE/                           # Backend (Node.js + Express)│   ├── genRSA.py         ← Generate RSA keys

    │   └── ...

    ├── package.json              # Frontend dependencies│   ├── server.js                 # Express API server│   ├── encode_v4.py      ← Encode message

    ├── vite.config.js            # Vite configuration

    └── ...│   ├── package.json              # Node.js dependencies│   ├── decode_v4.py      ← Decode message

```

│   ├── genRSA.py                 # RSA key generation│   ├── evaluate.py       ← Image comparison

## ✨ Features

│   └── tmp/                      # Temporary upload folder│   └── models_v4/        ← Trained models

- 🖼️ **Hide messages** in images using Deep Learning GAN

- 🔍 **Reveal messages** from stego images└── FE/                           # Frontend (React + Vite)│

- 🔐 **RSA-2048 + AES-256-CBC encryption** (optional)

- 🔑 **Generate RSA key pairs** (public/private)    ├── src/└── FE/                    ← Frontend (React + Vite)

- 🎨 **Modern React UI** with Tailwind CSS

- ⚡ **Fast API** with Express.js    │   ├── App.jsx               # Main React app    ├── src/

- 📱 **Responsive design** for mobile and desktop

- ✅ **Image validation** (minimum 512×512 pixels)    │   ├── components/    │   ├── App.jsx       ← Main app with tabs

- 🔄 **Auto-setup** - Virtual environment and dependencies installed automatically

    │   │   ├── EncodeTab.jsx     # Hide message tab    │   ├── components/

## 📋 Requirements

    │   │   ├── DecodeTab.jsx     # Reveal message tab    │   │   ├── GenKeyTab.jsx    ← Generate keys UI

### System Requirements

- **Node.js 16+**    │   │   └── GenKeyTab.jsx     # Generate RSA keys tab    │   │   ├── EncodeTab.jsx    ← Encode message UI

- **Python 3.8+**

- **8GB RAM** (recommended 16GB)    │   └── ...    │   │   └── DecodeTab.jsx    ← Decode message UI

- **~4GB disk space** (for PyTorch and dependencies)

    ├── package.json              # Frontend dependencies    │   └── ...

### Optional

- **GPU with CUDA** for faster encoding/decoding    ├── vite.config.js            # Vite configuration    ├── package.json

- **Nginx** for production deployment

- **PM2** for process management    └── ...    └── vite.config.js



## 🚀 Quick Start```



### Step 1: Install Node.js dependencies## ✨ Features## 🚀 Quick Start



```bash- 🖼️ **Hide messages** in images using Deep Learning GAN### 0. Setup Python Virtual Environment (First Time Only)

# Backend

cd BE- 🔍 **Reveal messages** from stego images

npm install

- 🔐 **RSA-2048 + AES-256-CBC encryption** (optional)The webApp uses its own Python virtual environment for standalone deployment.

# Frontend

cd ../FE- 🔑 **Generate RSA key pairs** (public/private)

npm install

```- 🎨 **Modern React UI** with Tailwind CSS```bash



### Step 2: Start Backend API- ⚡ **Fast API** with Express.js# Navigate to webApp folder



```bash- 📱 **Responsive design** for mobile and desktopcd webApp

cd BE

npm start- ✅ **Image validation** (minimum 512×512 pixels)

```

# Create virtual environment

Backend will **automatically**:

- ✅ Create Python virtual environment in `BE/venv/`## 📋 Requirementspython3 -m venv prjvenv

- ✅ Install Python packages from `BE/requirements.txt`

- ✅ Check for model file `BE/EN_DE_ep50_*.dat`### System Requirements# Activate it

- ✅ Start Express server on port 3000

- **Node.js 16+**source prjvenv/bin/activate # macOS/Linux

**No manual Python setup needed!** 🎉

- **Python 3.8+**# OR

### Step 3: Start Frontend Dev Server

- **8GB RAM** (recommended 16GB)prjvenv\Scripts\activate # Windows

```bash

cd FE- **~4GB disk space** (for PyTorch and dependencies)

npm run dev

```# Install Python dependencies



Frontend will start on http://localhost:5173### Optionalpip install -r requirements.txt



### Step 4: Build Frontend for Production- **GPU with CUDA** for faster encoding/decoding```



```bash- **Nginx** for production deployment

cd FE

npm run build- **PM2** for process management### 1. Setup Backend

```

## 🚀 Quick Start```bash

Output: `FE/dist/` (static files to serve with Nginx)

cd webApp/BE

## 🎯 Usage

### Step 1: Install Node.js dependenciesnpm install

### 1. Hide Message (Encode)

````

1. Go to **"Ẩn tin"** tab

2. Upload cover image (minimum 512×512 pixels)```bash

3. Enter secret message

4. **Optional:** Enable encryption and upload public key# Backend### 2. Setup Frontend

5. Click **"Ẩn tin nhắn"**

6. Download stego imagecd BE



### 2. Reveal Message (Decode)npm install```bash



1. Go to **"Trích xuất"** tabcd webApp/FE

2. Upload stego image

3. **Optional:** Upload private key if message was encrypted# Frontendnpm install

4. Click **"Trích xuất tin nhắn"**

5. View revealed messagecd ../FE```



### 3. Generate RSA Keysnpm install



1. Go to **"Tạo khóa"** tab```### 3. Run Backend Server

2. Click **"Tạo cặp khóa RSA"**

3. Download `public_key.pem` and `private_key.pem`

4. **Important:** Keep private key secret!

### Step 2: Install Python dependencies```bash

## 🔧 Configuration

cd webApp/BE

### Backend Configuration (BE/server.js)

The backend will **automatically** create a Python virtual environment and install dependencies on first run.npm start

```javascript

const PORT = process.env.PORT || 3000;````

const BE_DIR = __dirname;  // All Python files in BE/

const BE_VENV = path.join(BE_DIR, "venv");  // Virtual environment in BE/Or install manually:

```

```bashBackend will run on: **http://localhost:3000**

### Frontend Configuration (FE/src/...)

# From webApp folder

API endpoint is configured in component files. Update if backend runs on different port:

python3 -m venv venv### 4. Run Frontend Dev Server

```javascript

const API_URL = "http://localhost:3000";source venv/bin/activate  # On Windows: venv\Scripts\activate

```

pip install -r requirements.txtOpen a new terminal:

### Environment Variables

```

Create `.env` file in `BE/` folder:

```env````bash

PORT=3000

NODE_ENV=production### Step 3: Start Backend APIcd webApp/FE

```

npm run dev

## 📊 API Endpoints

```bash```

### POST /encode

Hide message in imagecd BE



**Request:**npm startFrontend will run on: **http://localhost:5173**

- `image`: Cover image file (multipart/form-data)

- `message`: Secret message (text)````

- `publicKey`: Public key file (optional)

### 5. Open in Browser

**Response:**

```jsonBackend will:

{

  "success": true,- ✅ Create Python virtual environment if not existsNavigate to: **http://localhost:5173**

  "stegoImageUrl": "/tmp/image/stego_12345.png",

  "message": "Encoded successfully"- ✅ Install Python packages automatically

}

```- ✅ Check for model fileYou'll see the Steganography V4 interface with three tabs:



### POST /decode- ✅ Start Express server on port 3000

Reveal message from stego image

- 🔑 **Generate Keys** - Create RSA keypair

**Request:**

- `image`: Stego image file (multipart/form-data)### Step 4: Start Frontend Dev Server- 🔐 **Encode Message** - Hide message in image

- `privateKey`: Private key file (optional)

- 🔓 **Decode Message** - Extract message from image

**Response:**

```json````bash

{

  "success": true,cd FE---

  "message": "Your secret message here"

}npm run dev

```

```## 📖 Usage

### POST /generate-keys

Generate RSA key pair



**Response:**Frontend will start on http://localhost:5173### Generate Keys

```json

{

  "success": true,

  "publicKey": "/tmp/metadata/public_key.pem",### Step 5: Build Frontend for Production1. Click the **"🔑 Generate Keys"** tab

  "privateKey": "/tmp/metadata/private_key.pem"

}2. Click **"🔑 Generate Keypair"**

```

```bash3. Download both **public_key.pem** and **private_key.pem**

## 🐳 Docker Deployment (Optional)

cd FE4. Keep the private key secure!

Create `Dockerfile`:

```dockerfilenpm run build

FROM node:18-slim

```### Encode Message

# Install Python

RUN apt-get update && apt-get install -y python3 python3-venv python3-pip



WORKDIR /appOutput: `FE/dist/` (static files to serve with Nginx)1. Click the **"🔐 Encode Message"** tab



# Copy app files2. Select a **cover image** (PNG/JPG)

COPY . .

## 🎯 Usage3. Select your **public key** (.pem file)

# Install Node dependencies

WORKDIR /app/BE4. Enter your **secret message**

RUN npm install

### 1. Hide Message (Encode)5. Click **"🔐 Encode Message"**

WORKDIR /app/FE

RUN npm install && npm run build6. Wait 10-30 seconds



WORKDIR /app1. Go to **"Ẩn tin"** tab7. Download the **stego image**



# Python venv will be created automatically on first run2. Upload cover image (minimum 512×512 pixels)

EXPOSE 3000

3. Enter secret message### Decode Message

CMD ["node", "BE/server.js"]

```4. **Optional:** Enable encryption and upload public key



Build and run:5. Click **"Ẩn tin nhắn"**1. Click the **"🔓 Decode Message"** tab

```bash

docker build -t customganstego-web .6. Download stego image2. Select the **stego image**

docker run -p 3000:3000 customganstego-web

```3. Select your **private key** (.pem file)



## 🌍 Production Deployment### 2. Reveal Message (Decode)4. Click **"🔓 Decode Message"**



### Option 1: PM2 (Process Manager)5. The hidden message will be revealed!



```bash1. Go to **"Trích xuất"** tab

# Install PM2

npm install -g pm22. Upload stego image---



# Start backend with PM23. **Optional:** Upload private key if message was encrypted

cd BE

pm2 start server.js --name "stegan-api"4. Click **"Trích xuất tin nhắn"**## 🔧 API Endpoints



# Auto-restart on system boot5. View revealed message

pm2 startup

pm2 save### POST /rsa-genkey



# Monitor### 3. Generate RSA Keys

pm2 logs stegan-api

pm2 monitGenerate RSA keypair.

```

1. Go to **"Tạo khóa"** tab

### Option 2: Nginx + PM2

2. Click **"Tạo cặp khóa RSA"****Request:** None

1. **Build frontend:**

```bash3. Download `public_key.pem` and `private_key.pem`

cd FE

npm run build4. **Important:** Keep private key secret!**Response:**

```



2. **Configure Nginx:**

```nginx## 🔧 Configuration```json

server {

    listen 80;{

    server_name your-domain.com;

### Backend Configuration (BE/server.js)  "public_key": "<base64>",

    # Frontend (static files)

    location / {  "private_key": "<base64>",

        root /path/to/webApp/FE/dist;

        try_files $uri $uri/ /index.html;```javascript  "public_name": "public_xxx.pem",

    }

const PORT = process.env.PORT || 3000;  "private_name": "private_xxx.pem"

    # Backend API

    location /api/ {const WEBAPP_ROOT = path.resolve(__dirname, "..");}

        proxy_pass http://localhost:3000/;

        proxy_http_version 1.1;const WEBAPP_VENV = path.join(WEBAPP_ROOT, "venv");```

        proxy_set_header Upgrade $http_upgrade;

        proxy_set_header Connection 'upgrade';````

        proxy_set_header Host $host;

        proxy_cache_bypass $http_upgrade;### POST /encode

        proxy_set_header X-Real-IP $remote_addr;

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;### Frontend Configuration (FE/src/...)



        # Increase timeouts for large filesEncode message into image.

        proxy_connect_timeout 600;

        proxy_send_timeout 600;API endpoint is configured in component files. Update if backend runs on different port:

        proxy_read_timeout 600;

        send_timeout 600;**Request:** `multipart/form-data`



        # Increase max body size for image uploads````javascript

        client_max_body_size 50M;

    }const API_URL = "http://localhost:3000";- `cover` (file) - Cover image

}

``````- `public_key` (file, optional) - Public key



3. **Start backend with PM2:**- `message` (string) - Secret message

```bash

cd BE### Environment Variables

pm2 start server.js --name "stegan-api"

```**Response:** Stego image file (download)



4. **Enable HTTPS (optional):**Create `.env` file in `BE/` folder:

```bash

sudo apt install certbot python3-certbot-nginx```env### POST /decode

sudo certbot --nginx -d your-domain.com

```PORT=3000



## 🔍 TroubleshootingNODE_ENV=productionDecode message from image.



### ❌ "Model file not found"````

```bash

# Check if model exists in BE folder**Request:** `multipart/form-data`

ls BE/EN_DE_ep50_*.dat

## 📊 API Endpoints

# If not, copy from results folder

cp ../results/model/EN_DE_ep50_*.dat BE/- `stego` (file) - Stego image

```

### POST /encode- `private_key` (file, optional) - Private key

### ❌ "Virtual environment creation failed"

```bashHide message in image

# Install python3-venv

sudo apt install python3-venv python3-pip**Response:**



# Create manually**Request:**

cd BE

python3 -m venv venv- `image`: Cover image file (multipart/form-data)```json

source venv/bin/activate

pip install -r requirements.txt- `message`: Secret message (text){

```

- `publicKey`: Public key file (optional) "message": "decoded secret message"

### ❌ "Module not found" errors

```bash}

# Ensure all Python modules are in BE folder

ls BE/*.py**Response:**```



# Should see: encoder.py, decoder.py, critic.py, enhancedstegan.py, genRSA.py```json

```

{---

### ❌ "Port 3000 already in use"

```bash  "success": true,

# Change port in BE/server.js or use environment variable

PORT=4000 npm start  "stegoImageUrl": "/tmp/image/stego_12345.png",## 🛠️ Development

```

  "message": "Encoded successfully"

### ❌ "Image too small" error

- Use images **≥ 512×512 pixels**}### Backend Development

- Recommended: 1024×768 or larger

```

### ❌ Backend crashes on large images

```bash```````bash

# Increase Node.js memory

node --max-old-space-size=4096 server.js### POST /decodecd webApp/BE



# Or in PM2Reveal message from stego imagenpm start

pm2 start server.js --node-args="--max-old-space-size=4096"

```# Server runs on port 3000



## 📊 Performance Tips**Request:**```



### For Production:- `image`: Stego image file (multipart/form-data)

1. **Enable Nginx gzip compression**

2. **Use CDN for static assets**- `privateKey`: Private key file (optional)### Frontend Development

3. **Enable HTTP/2**

4. **Use PM2 cluster mode:**

   ```bash

   pm2 start server.js -i max**Response:**```bash

   ```

5. **Cache static files** (images, CSS, JS)```jsoncd webApp/FE



### For Development:{npm run dev

1. **Use GPU** if available (auto-detected)

2. **Reduce image size** for faster processing  "success": true,# Dev server runs on port 5173 with hot reload

3. **Clear tmp folder** periodically:

   ```bash  "message": "Your secret message here"```

   rm -rf BE/tmp/*

   ```}



## 🔐 Security Considerations```### Build Frontend for Production



1. **HTTPS required** for production

2. **Rate limiting** recommended (use express-rate-limit)

3. **File upload validation** (size, type)### POST /generate-keys```bash

4. **Private keys** should never be uploaded to server

5. **Sanitize user inputs**Generate RSA key paircd webApp/FE

6. **Set proper CORS** headers

npm run build

Example rate limiting:

```javascript**Response:**# Output in FE/dist/

const rateLimit = require("express-rate-limit");

```json```

const limiter = rateLimit({

  windowMs: 15 * 60 * 1000, // 15 minutes{

  max: 100 // max 100 requests per 15 min

});  "success": true,---



app.use("/api/", limiter);  "publicKey": "/tmp/metadata/public_key.pem",

```

  "privateKey": "/tmp/metadata/private_key.pem"## 📝 Requirements

## 📚 Technology Stack

}

### Backend

- **Node.js** - JavaScript runtime```### Backend

- **Express.js** - Web framework

- **Multer** - File upload handling

- **Python** - Steganography processing

- **PyTorch** - Deep learning framework## 🐳 Docker Deployment (Optional)- Node.js 16+



### Frontend- Python 3.8+ (installed in `webApp/prjvenv/`)

- **React** - UI library

- **Vite** - Build toolCreate `Dockerfile`:- Python packages (see `requirements.txt`):

- **Tailwind CSS** - Styling

- **Axios** - HTTP client (if used)```dockerfile  - torch



### AI/MLFROM node:18-slim  - torchvision

- **BasicEncoder/BasicDecoder** - Custom GAN architecture

- **data_depth=2, hidden_size=32** - Model parameters  - Pillow

- **Reed-Solomon** - Error correction

- **zlib** - Compression# Install Python  - numpy



## 📝 File StructureRUN apt-get update && apt-get install -y python3 python3-venv python3-pip  - pycryptodome



```  - scikit-image

webApp/

├── README.md                    # This fileWORKDIR /app  - opencv-python

├── BE/

│   ├── venv/                    # Python virtual environment

│   ├── *.dat                    # Pre-trained model

│   ├── *.py                     # Python modules# Copy app files### Frontend

│   ├── requirements.txt         # Python deps

│   ├── server.js               # Main serverCOPY . .

│   ├── package.json            # Node deps

│   └── tmp/                    # Uploads- Node.js 16+

└── FE/

    ├── src/# Install dependencies- Modern browser (Chrome, Firefox, Safari, Edge)

    │   ├── App.jsx             # Main component

    │   └── components/         # React componentsWORKDIR /app/BE

    └── dist/                   # Build output

```RUN npm install---



## 🆘 Support



For issues:WORKDIR /app/FE## 🔐 Security Notes

1. Check this README

2. Check terminal/console outputRUN npm install && npm run build

3. Check `BE/tmp/` for error logs

4. Verify model file exists in `BE/`- This app runs Python scripts on the server - use in trusted environments only

5. Ensure Python packages installed in `BE/venv/`

WORKDIR /app- Keep private keys secure and never share them

## 📄 License

- For production, add authentication and HTTPS

Project CNTT - Deep Learning Steganography

# Python venv will be created automatically on first run- Backend validates file types but additional security measures recommended

---

EXPOSE 3000

**Built with:** Node.js, Express, React, Vite, PyTorch, Tailwind CSS

---

**Server auto-setup:** ✅ Virtual environment in BE/, ✅ Dependencies, ✅ Model check

CMD ["node", "BE/server.js"]

**Ready for:** Development, Production, Docker, aaPanel, Nginx

```## 🐛 Troubleshooting

**All files in BE folder:** ✅ Model, ✅ Python modules, ✅ Virtual environment, ✅ Requirements



Build and run:### Backend Issues

```bash

docker build -t customganstego-web .**Port 3000 already in use:**

docker run -p 3000:3000 customganstego-web

``````bash

# Change PORT in BE/server.js or:

## 🌍 Production DeploymentPORT=3001 npm start

````````

### Option 1: PM2 (Process Manager)

**Python not found:**

````bash

# Install PM2```bash

npm install -g pm2# Create and activate local virtual environment in webApp/

cd webApp

# Start backend with PM2python3 -m venv prjvenv

cd BEsource prjvenv/bin/activate

pm2 start server.js --name "stegan-api"pip install -r requirements.txt

````

# Auto-restart on system boot

pm2 startup**Python packages missing:**

pm2 save

```bash

# Monitorcd webApp

pm2 logs stegan-apisource prjvenv/bin/activate

pm2 monitpip install -r requirements.txt

```

### Option 2: Nginx + PM2**Model not found:**

1. **Build frontend:**```bash

````bash# Ensure models_v4 folder exists in BE/

cd FEls -la BE/models_v4/best_model.pth

npm run build```

````

### Frontend Issues

2. **Configure Nginx:**

````nginx**API calls failing:**

server {

    listen 80;- Check backend is running on port 3000

    server_name your-domain.com;- Check CORS is enabled in BE/server.js

- Update API_URL in component files if needed

    # Frontend (static files)

    location / {**Build errors:**

        root /path/to/webApp/FE/dist;

        try_files $uri $uri/ /index.html;```bash

    }cd FE

rm -rf node_modules package-lock.json

    # Backend APInpm install

    location /api/ {```

        proxy_pass http://localhost:3000/;

        proxy_http_version 1.1;---

        proxy_set_header Upgrade $http_upgrade;

        proxy_set_header Connection 'upgrade';## 📊 Features

        proxy_set_header Host $host;

        proxy_cache_bypass $http_upgrade;### ✅ Completed

        proxy_set_header X-Real-IP $remote_addr;

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;- [x] Generate RSA keypair (1024-4096 bits)

        - [x] Encode message with RSA + AES-256-CBC encryption

        # Increase timeouts for large files- [x] Plain text mode (no encryption)

        proxy_connect_timeout 600;- [x] Decode message with private key

        proxy_send_timeout 600;- [x] React UI with tabs

        proxy_read_timeout 600;- [x] File upload/download

        send_timeout 600;- [x] Real-time feedback and loading states

        - [x] Error handling

        # Increase max body size for image uploads- [x] Responsive design

        client_max_body_size 50M;

    }### 🚧 Future Enhancements

}

```- [ ] Image comparison/evaluation UI

- [ ] Batch processing

3. **Start backend with PM2:**- [ ] User authentication

```bash- [ ] Message history

cd BE- [ ] Drag & drop file uploads

pm2 start server.js --name "stegan-api"- [ ] Image preview before encoding

```- [ ] PSNR/SSIM metrics display

- [ ] Progress bars for long operations

4. **Enable HTTPS (optional):**

```bash---

sudo apt install certbot python3-certbot-nginx

sudo certbot --nginx -d your-domain.com## 🎉 Quick Commands Reference

````

````bash

### Option 3: aaPanel / cPanel# First time setup

cd webApp

1. Upload files to `/www/wwwroot/your-site/`python3 -m venv prjvenv

2. Create Node.js app in panelsource prjvenv/bin/activate  # or prjvenv\Scripts\activate on Windows

3. Set startup file: `BE/server.js`pip install -r requirements.txt

4. Configure Nginx reverse proxy

5. Start app# Install Node dependencies

cd BE && npm install && cd ../FE && npm install && cd ..

## 🔍 Troubleshooting

# Start backend (from webApp folder)

### ❌ "Model file not found"cd BE && npm start

```bash

# Check if model exists# Start frontend (new terminal, from webApp folder)

ls webApp/EN_DE_ep50_*.datcd FE && npm run dev

````

# If not, copy from results folder

cp ../results/model/EN*DE_ep50*\*.dat .**That's it! Happy Steganography! 🔐**

````

---

### ❌ "Virtual environment creation failed"

```bash_Last updated: November 1, 2025_

# Install python3-venv
sudo apt install python3-venv python3-pip

# Create manually
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

### ❌ "Module not found" errors

```bash
# Ensure Python modules are in webApp folder
cp ../encoder.py ../decoder.py ../critic.py ../enhancedstegan.py .
```

### ❌ "Port 3000 already in use"

```bash
# Change port in BE/server.js or use environment variable
PORT=4000 npm start
```

### ❌ "Image too small" error

- Use images **≥ 512×512 pixels**
- Recommended: 1024×768 or larger

### ❌ Backend crashes on large images

```bash
# Increase Node.js memory
node --max-old-space-size=4096 server.js

# Or in PM2
pm2 start server.js --node-args="--max-old-space-size=4096"
```

## 📊 Performance Tips

### For Production:

1. **Enable Nginx gzip compression**
2. **Use CDN for static assets**
3. **Enable HTTP/2**
4. **Use PM2 cluster mode:**
   ```bash
   pm2 start server.js -i max
   ```
5. **Cache static files** (images, CSS, JS)

### For Development:

1. **Use GPU** if available (auto-detected)
2. **Reduce image size** for faster processing
3. **Clear tmp folder** periodically:
   ```bash
   rm -rf BE/tmp/*
   ```

## 🔐 Security Considerations

1. **HTTPS required** for production
2. **Rate limiting** recommended (use express-rate-limit)
3. **File upload validation** (size, type)
4. **Private keys** should never be uploaded to server
5. **Sanitize user inputs**
6. **Set proper CORS** headers

Example rate limiting:

```javascript
const rateLimit = require("express-rate-limit");

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // max 100 requests per 15 min
});

app.use("/api/", limiter);
```

## 📚 Technology Stack

### Backend

- **Node.js** - JavaScript runtime
- **Express.js** - Web framework
- **Multer** - File upload handling
- **Python** - Steganography processing
- **PyTorch** - Deep learning framework

### Frontend

- **React** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

### AI/ML

- **BasicEncoder/BasicDecoder** - Custom GAN architecture
- **data_depth=2, hidden_size=32** - Model parameters
- **Reed-Solomon** - Error correction
- **zlib** - Compression

## 📝 Development

### File Structure

```
webApp/
├── venv/                    # Python virtual environment
├── *.dat                    # Pre-trained model
├── *.py                     # Python modules
├── requirements.txt         # Python deps
├── BE/
│   ├── server.js           # Main server
│   ├── package.json        # Node deps
│   └── tmp/                # Uploads
└── FE/
    ├── src/
    │   ├── App.jsx         # Main component
    │   └── components/     # React components
    └── dist/               # Build output
```

### Adding New Features

1. **Backend:** Edit `BE/server.js`
2. **Frontend:** Add component in `FE/src/components/`
3. **Python processing:** Edit `enhancedstegan.py`

### Running Tests

```bash
# Backend
cd BE
npm test  # if tests exist

# Frontend
cd FE
npm test
```

## 🆘 Support

For issues:

1. Check this README
2. Check terminal/console output
3. Check `BE/tmp/` for error logs
4. Verify model file exists
5. Ensure Python packages installed

## 📄 License

Project CNTT - Deep Learning Steganography

---

**Built with:** Node.js, Express, React, Vite, PyTorch, Tailwind CSS

**Server auto-setup:** ✅ Virtual environment, ✅ Dependencies, ✅ Model check

**Ready for:** Development, Production, Docker, aaPanel, Nginx
