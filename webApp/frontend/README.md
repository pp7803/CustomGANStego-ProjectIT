# CustomGANStego Frontend

React + Vite frontend for CustomGANStego steganography application.

## Features

- **Encode**: Hide secret messages in images with optional RSA+AES encryption
- **Decode**: Extract hidden messages from stego images (upload file or use URL)
- **Reverse**: Recover original image from stego image
- **Compare**: Calculate PSNR, SSIM, MSE metrics between images
- **Generate RSA**: Create RSA key pairs for encryption

## Setup

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The application will run on http://localhost:3000

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

## Configuration

### API Endpoint

The API endpoint is configured in `src/api.js`:

- **Development**: Proxies to `http://localhost:3012` via Vite proxy
- **Production**: Uses `https://apistegan.ppdeveloper.xyz`

To change the production API endpoint, modify `API_BASE_URL` in `src/api.js`.

### Port

To change the development port, edit `vite.config.js`:

```javascript
export default defineConfig({
  server: {
    port: 3000, // Change this
  },
});
```

## Deployment

### Deploy to Static Hosting (Nginx, Apache, etc.)

1. Build the project:

   ```bash
   npm run build
   ```

2. Copy the `dist/` folder contents to your web server

3. Configure your server to:
   - Serve `index.html` for all routes (SPA mode)
   - Set proper CORS headers if needed

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Technology Stack

- **React 18**: UI framework
- **Vite 5**: Build tool and dev server
- **Axios**: HTTP client for API calls
- **CSS3**: Styling with gradients and animations

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── EncodeTab.jsx      # Encode message in image
│   │   ├── DecodeTab.jsx      # Decode message from image
│   │   ├── ReverseTab.jsx     # Recover original image
│   │   ├── CompareTab.jsx     # Compare images (metrics)
│   │   └── GenRSATab.jsx      # Generate RSA keys
│   ├── App.jsx                # Main app with tabs
│   ├── api.js                 # API service layer
│   ├── main.jsx               # Entry point
│   └── index.css              # Global styles
├── index.html                 # HTML template
├── vite.config.js             # Vite configuration
└── package.json               # Dependencies
```

## API Integration

All API calls are centralized in `src/api.js`. The frontend communicates with the backend using the following endpoints:

- `GET /health` - Health check
- `POST /encode` - Encode message in image
- `POST /decode` - Decode message from image
- `POST /reverse` - Recover original image
- `POST /compare` - Compare two images
- `POST /genrsa` - Generate RSA key pair
- `GET /files/<filename>` - Serve output files

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

Same as main project.
