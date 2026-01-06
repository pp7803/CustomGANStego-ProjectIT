#!/usr/bin/env python3
"""
macOS Steganography App - GAN-based Steganography với RSA Encryption
====================================================================

Ứng dụng steganography đầy đủ với các chức năng:
- Encode: Giấu tin vào ảnh
- Decode: Trích xuất tin từ ảnh
- Reverse: Khôi phục ảnh gốc
- GenRSA: Tạo khóa RSA
- Compare: So sánh và tính metrics PSNR/SSIM
- Visualization: Hiển thị ảnh comparison

Author: CustomGANStego Team
"""

import sys
import os
import re
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from PIL import Image, ImageTk
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
import psutil

parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from enhancedstegan import encode_message, decode_message, reverse_hiding


def find_best_model(models_dir=None):
    """
    Tìm model tốt nhất dựa trên accuracy và PSNR từ tên file.
    Hỗ trợ cả development mode và bundled app.
    
    Expected filename pattern:
    EN_DE_REV_ep016_acc0.9901_psnr39.22_rpsnr37.24_20251225_164557.dat
    """
    if models_dir is None:
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
            possible_dirs = [
                os.path.join(bundle_dir, 'results', 'model'),
                os.path.join(os.path.dirname(sys.executable), '..', 'Resources', 'results', 'model'),
            ]
        else:
            possible_dirs = [
                str(parent_dir / 'results' / 'model'),
            ]
        
        for dir_path in possible_dirs:
            if os.path.isdir(dir_path):
                models_dir = dir_path
                break
    
    if not models_dir or not os.path.isdir(models_dir):
        return None

    best = None
    best_acc = -1.0
    best_psnr = -1.0
    pattern = re.compile(r"acc([0-9]*\.?[0-9]+).*psnr([0-9]*\.?[0-9]+)")

    for fname in os.listdir(models_dir):
        if not fname.endswith('.dat'):
            continue
        m = pattern.search(fname)
        if not m:
            continue
        try:
            acc = float(m.group(1))
            psnr = float(m.group(2))
        except Exception:
            continue

        if acc > best_acc or (acc == best_acc and psnr > best_psnr):
            best_acc = acc
            best_psnr = psnr
            best = os.path.join(models_dir, fname)

    return best

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GAN Steganography - CustomGANStego")
        self.root.geometry("1200x800")
        
        # Set theme based on OS
        style = ttk.Style()
        if sys.platform == 'darwin':  # macOS
            style.theme_use('aqua')
        elif sys.platform == 'win32':  # Windows
            style.theme_use('vista')
        else:  # Linux and others
            style.theme_use('clam')
        
        self.model_path = find_best_model()
        if self.model_path:
            model_name = os.path.basename(self.model_path)
            print(f"Loaded model: {model_name}")
        else:
            print("No model found - operations may not work")
        
        self.cover_image_path = None
        self.stego_image_path = None
        self.secret_text = tk.StringVar()
        self.use_encryption = tk.BooleanVar(value=False)
        self.public_key_path = None
        self.private_key_path = None
        
        self.process = psutil.Process()
        self.ram_usage_mb = 0
        self.peak_ram_mb = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.encode_tab = ttk.Frame(notebook)
        self.decode_tab = ttk.Frame(notebook)
        self.reverse_tab = ttk.Frame(notebook)
        self.genrsa_tab = ttk.Frame(notebook)
        self.compare_tab = ttk.Frame(notebook)
        self.debug_tab = ttk.Frame(notebook)
        
        notebook.add(self.encode_tab, text="Encode")
        notebook.add(self.decode_tab, text="Decode")
        notebook.add(self.reverse_tab, text="Reverse")
        notebook.add(self.genrsa_tab, text="GenRSA")
        notebook.add(self.compare_tab, text="Compare")
        notebook.add(self.debug_tab, text="Debug")
        
        self.setup_encode_tab()
        self.setup_decode_tab()
        self.setup_reverse_tab()
        self.setup_genrsa_tab()
        self.setup_compare_tab()
        self.setup_debug_tab()
        
        self.setup_console_redirect()
        
    def setup_encode_tab(self):
        """Setup Encode tab"""
        canvas = tk.Canvas(self.encode_tab)
        scrollbar = ttk.Scrollbar(self.encode_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to update window width
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame = ttk.Frame(scrollable_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        title = ttk.Label(frame, text="Encode - Giấu tin vào ảnh", 
                         font=('Helvetica', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        img_frame = ttk.LabelFrame(frame, text="1. Chọn ảnh Cover", padding=10)
        img_frame.pack(fill='x', pady=10)
        
        self.encode_cover_label = ttk.Label(img_frame, text="Chưa chọn ảnh")
        self.encode_cover_label.pack(side='left', padx=5)
        
        ttk.Button(img_frame, text="Chọn ảnh...", 
                  command=self.select_encode_cover).pack(side='right', padx=5)
        
        msg_frame = ttk.LabelFrame(frame, text="2. Nhập tin cần giấu", padding=10)
        msg_frame.pack(fill='both', expand=True, pady=10)
        
        self.encode_text = scrolledtext.ScrolledText(msg_frame, height=8, wrap=tk.WORD)
        self.encode_text.pack(fill='both', expand=True)
        
        enc_frame = ttk.LabelFrame(frame, text="3. Mã hóa (tùy chọn)", padding=10)
        enc_frame.pack(fill='x', pady=10)
        
        ttk.Checkbutton(enc_frame, text="Sử dụng mã hóa RSA+AES", 
                       variable=self.use_encryption,
                       command=self.toggle_encryption).pack(anchor='w')
        
        key_frame = ttk.Frame(enc_frame)
        key_frame.pack(fill='x', pady=5)
        
        self.encode_pubkey_label = ttk.Label(key_frame, text="Public key: chưa chọn")
        self.encode_pubkey_label.pack(side='left', padx=5)
        
        self.encode_pubkey_btn = ttk.Button(key_frame, text="Chọn public key...", 
                                           command=self.select_public_key, state='disabled')
        self.encode_pubkey_btn.pack(side='right', padx=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Encode", 
                  command=self.run_encode, style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Clear", 
                  command=self.clear_encode).pack(side='right', padx=5)
        
        self.encode_status = ttk.Label(frame, text="", foreground='blue')
        self.encode_status.pack(pady=5)
        
    def setup_decode_tab(self):
        """Setup Decode tab"""
        canvas = tk.Canvas(self.decode_tab)
        scrollbar = ttk.Scrollbar(self.decode_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to update window width
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame = ttk.Frame(scrollable_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        title = ttk.Label(frame, text="Decode - Trích xuất tin từ ảnh", 
                         font=('Helvetica', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        img_frame = ttk.LabelFrame(frame, text="1. Chọn ảnh Stego", padding=10)
        img_frame.pack(fill='x', pady=10)
        
        self.decode_stego_label = ttk.Label(img_frame, text="Chưa chọn ảnh")
        self.decode_stego_label.pack(side='left', padx=5)
        
        ttk.Button(img_frame, text="Chọn ảnh...", 
                  command=self.select_decode_stego).pack(side='right', padx=5)
        
        enc_frame = ttk.LabelFrame(frame, text="2. Giải mã (nếu có mã hóa)", padding=10)
        enc_frame.pack(fill='x', pady=10)
        
        self.decode_use_decrypt = tk.BooleanVar(value=False)
        ttk.Checkbutton(enc_frame, text="Giải mã RSA+AES", 
                       variable=self.decode_use_decrypt,
                       command=self.toggle_decryption).pack(anchor='w')
        
        key_frame = ttk.Frame(enc_frame)
        key_frame.pack(fill='x', pady=5)
        
        self.decode_privkey_label = ttk.Label(key_frame, text="Private key: chưa chọn")
        self.decode_privkey_label.pack(side='left', padx=5)
        
        self.decode_privkey_btn = ttk.Button(key_frame, text="Chọn private key...", 
                                            command=self.select_private_key, state='disabled')
        self.decode_privkey_btn.pack(side='right', padx=5)
        
        msg_frame = ttk.LabelFrame(frame, text="3. Tin đã trích xuất", padding=10)
        msg_frame.pack(fill='both', expand=True, pady=10)
        
        self.decode_text = scrolledtext.ScrolledText(msg_frame, height=10, wrap=tk.WORD)
        self.decode_text.pack(fill='both', expand=True)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Decode", 
                  command=self.run_decode, style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Save", 
                  command=self.save_decoded).pack(side='right', padx=5)
        
        self.decode_status = ttk.Label(frame, text="", foreground='blue')
        self.decode_status.pack(pady=5)
        
    def setup_reverse_tab(self):
        """Setup Reverse tab"""
        canvas = tk.Canvas(self.reverse_tab)
        scrollbar = ttk.Scrollbar(self.reverse_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to update window width
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame = ttk.Frame(scrollable_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        title = ttk.Label(frame, text="Reverse - Khôi phục ảnh gốc", 
                         font=('Helvetica', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        img_frame = ttk.LabelFrame(frame, text="1. Chọn ảnh Stego", padding=10)
        img_frame.pack(fill='x', pady=10)
        
        self.reverse_stego_label = ttk.Label(img_frame, text="Chưa chọn ảnh")
        self.reverse_stego_label.pack(side='left', padx=5)
        
        ttk.Button(img_frame, text="Chọn ảnh...", 
                  command=self.select_reverse_stego).pack(side='right', padx=5)
        
        preview_frame = ttk.LabelFrame(frame, text="2. Xem trước kết quả", padding=10)
        preview_frame.pack(fill='both', expand=True, pady=10)
        
        comparison_frame = ttk.Frame(preview_frame)
        comparison_frame.pack(fill='both', expand=True)
        
        stego_frame = ttk.Frame(comparison_frame)
        stego_frame.pack(side='left', fill='both', expand=True, padx=5)
        ttk.Label(stego_frame, text="Ảnh Stego", font=('Helvetica', 12, 'bold')).pack()
        self.reverse_stego_preview = ttk.Label(stego_frame, text="Chưa có ảnh")
        self.reverse_stego_preview.pack(fill='both', expand=True)
        
        recovered_frame = ttk.Frame(comparison_frame)
        recovered_frame.pack(side='right', fill='both', expand=True, padx=5)
        ttk.Label(recovered_frame, text="Ảnh đã khôi phục", font=('Helvetica', 12, 'bold')).pack()
        self.reverse_recovered_preview = ttk.Label(recovered_frame, text="Chưa có kết quả")
        self.reverse_recovered_preview.pack(fill='both', expand=True)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Reverse", 
                  command=self.run_reverse, style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Save", 
                  command=self.save_reversed).pack(side='right', padx=5)
        
        self.reverse_status = ttk.Label(frame, text="", foreground='blue')
        self.reverse_status.pack(pady=5)
        
        self.reversed_image_path = None
        
    def setup_genrsa_tab(self):
        """Setup GenRSA tab"""
        canvas = tk.Canvas(self.genrsa_tab)
        scrollbar = ttk.Scrollbar(self.genrsa_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to update window width
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame = ttk.Frame(scrollable_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        title = ttk.Label(frame, text="GenRSA - Tạo cặp khóa RSA", 
                         font=('Helvetica', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        size_frame = ttk.LabelFrame(frame, text="1. Chọn độ dài khóa", padding=10)
        size_frame.pack(fill='x', pady=10)
        
        self.key_size = tk.IntVar(value=2048)
        for size in [1024, 2048, 3072, 4096]:
            ttk.Radiobutton(size_frame, text=f"{size} bits", 
                           variable=self.key_size, value=size).pack(anchor='w')
        
        path_frame = ttk.LabelFrame(frame, text="2. Chọn thư mục lưu", padding=10)
        path_frame.pack(fill='x', pady=10)
        
        self.genrsa_dir_label = ttk.Label(path_frame, text="Chưa chọn thư mục")
        self.genrsa_dir_label.pack(side='left', padx=5)
        
        ttk.Button(path_frame, text="Chọn thư mục...", 
                  command=self.select_genrsa_dir).pack(side='right', padx=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Tạo khóa", 
                  command=self.run_genrsa, style='Accent.TButton').pack(side='right', padx=5)
        
        output_frame = ttk.LabelFrame(frame, text="Kết quả", padding=10)
        output_frame.pack(fill='both', expand=True, pady=10)
        
        self.genrsa_output = scrolledtext.ScrolledText(output_frame, height=15, wrap=tk.WORD)
        self.genrsa_output.pack(fill='both', expand=True)
        
        self.genrsa_dir = None
        
    def setup_compare_tab(self):
        """Setup Compare tab"""
        canvas = tk.Canvas(self.compare_tab)
        scrollbar = ttk.Scrollbar(self.compare_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to update window width
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame = ttk.Frame(scrollable_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        title = ttk.Label(frame, text="Compare - So sánh và tính metrics", 
                         font=('Helvetica', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        sel_frame = ttk.Frame(frame)
        sel_frame.pack(fill='x', pady=10)
        
        img1_frame = ttk.LabelFrame(sel_frame, text="Ảnh 1 (Cover/Original)", padding=10)
        img1_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.compare_img1_label = ttk.Label(img1_frame, text="Chưa chọn")
        self.compare_img1_label.pack()
        ttk.Button(img1_frame, text="Chọn ảnh 1...", 
                  command=self.select_compare_img1).pack(pady=5)
        
        img2_frame = ttk.LabelFrame(sel_frame, text="Ảnh 2 (Stego/Recovered)", padding=10)
        img2_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        self.compare_img2_label = ttk.Label(img2_frame, text="Chưa chọn")
        self.compare_img2_label.pack()
        ttk.Button(img2_frame, text="Chọn ảnh 2...", 
                  command=self.select_compare_img2).pack(pady=5)
        
        metrics_frame = ttk.LabelFrame(frame, text="Metrics", padding=10)
        metrics_frame.pack(fill='both', expand=True, pady=10)
        
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=10, wrap=tk.WORD,
                                                      font=('Courier', 12))
        self.metrics_text.pack(fill='both', expand=True)
        
        preview_frame = ttk.LabelFrame(frame, text="So sánh trực quan", padding=10)
        preview_frame.pack(fill='both', expand=True, pady=10)
        
        self.compare_preview = ttk.Label(preview_frame, text="Chưa có kết quả")
        self.compare_preview.pack(fill='both', expand=True)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Tính Metrics", 
                  command=self.run_compare, style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Save PNG", 
                  command=self.save_comparison).pack(side='right', padx=5)
        
        self.compare_img1_path = None
        self.compare_img2_path = None
        self.comparison_image = None
        
    def select_encode_cover(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh cover",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if path:
            self.cover_image_path = path
            self.encode_cover_label.config(text=Path(path).name)
            
    def toggle_encryption(self):
        if self.use_encryption.get():
            self.encode_pubkey_btn.config(state='normal')
        else:
            self.encode_pubkey_btn.config(state='disabled')
            
    def select_public_key(self):
        path = filedialog.askopenfilename(
            title="Chọn public key",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")]
        )
        if path:
            self.public_key_path = path
            self.encode_pubkey_label.config(text=f"Public key: {Path(path).name}")
            
    def clear_encode(self):
        self.encode_text.delete('1.0', tk.END)
        self.encode_status.config(text="")
        
    def run_encode(self):
        if not self.cover_image_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh cover!")
            return
            
        message = self.encode_text.get('1.0', tk.END).strip()
        if not message:
            messagebox.showerror("Lỗi", "Vui lòng nhập tin cần giấu!")
            return
            
        if self.use_encryption.get() and not self.public_key_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn public key!")
            return
            
        output_path = filedialog.asksaveasfilename(
            title="Lưu ảnh stego",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not output_path:
            return
            
        def encode_thread():
            try:
                start_ram = self.process.memory_info().rss / (1024 * 1024)  # MB
                start_time = time.time()
                
                self.encode_status.config(text="Đang encode...", foreground='blue')
                self.root.update()
                
                final_message = message
                if self.use_encryption.get() and CRYPTO_AVAILABLE:
                    with open(self.public_key_path, 'rb') as f:
                        public_key = RSA.import_key(f.read())
                    
                    aes_key = get_random_bytes(16)
                    cipher_aes = AES.new(aes_key, AES.MODE_CBC)
                    ct_bytes = cipher_aes.encrypt(pad(message.encode('utf-8'), AES.block_size))
                    
                    cipher_rsa = PKCS1_OAEP.new(public_key)
                    enc_aes_key = cipher_rsa.encrypt(aes_key)
                    
                    import struct
                    final_message = struct.pack('<I', len(enc_aes_key)) + enc_aes_key + cipher_aes.iv + ct_bytes
                    final_message = final_message.hex()  # Convert to hex string
                
                encode_message(self.cover_image_path, final_message, output_path, 
                             model_path=self.model_path)
                
                end_ram = self.process.memory_info().rss / (1024 * 1024)  # MB
                elapsed_time = time.time() - start_time
                ram_used = end_ram - start_ram
                self.peak_ram_mb = max(self.peak_ram_mb, end_ram)
                
                status_msg = f"Lưu: {Path(output_path).name} | RAM: {ram_used:.1f}MB | Time: {elapsed_time:.2f}s"
                self.encode_status.config(text=status_msg, foreground='green')
                
                self.update_ram_info()
                
                messagebox.showinfo("Thành công", f"Đã encode và lưu vào:\n{output_path}\n\nRAM used: {ram_used:.1f} MB\nTime: {elapsed_time:.2f}s")
                
            except Exception as e:
                self.encode_status.config(text=f"Loi: {str(e)}", foreground='red')
                messagebox.showerror("Lỗi", f"Encode thất bại:\n{str(e)}")
        
        threading.Thread(target=encode_thread, daemon=True).start()
        
    def select_decode_stego(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh stego",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if path:
            self.stego_image_path = path
            self.decode_stego_label.config(text=Path(path).name)
            
    def toggle_decryption(self):
        if self.decode_use_decrypt.get():
            self.decode_privkey_btn.config(state='normal')
        else:
            self.decode_privkey_btn.config(state='disabled')
            
    def select_private_key(self):
        path = filedialog.askopenfilename(
            title="Chọn private key",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")]
        )
        if path:
            self.private_key_path = path
            self.decode_privkey_label.config(text=f"Private key: {Path(path).name}")
            
    def run_decode(self):
        if not self.stego_image_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh stego!")
            return
            
        if self.decode_use_decrypt.get() and not self.private_key_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn private key!")
            return
            
        def decode_thread():
            try:
                start_ram = self.process.memory_info().rss / (1024 * 1024)  # MB
                start_time = time.time()
                
                self.decode_status.config(text="⏳ Đang decode...", foreground='blue')
                self.root.update()
                
                message = decode_message(self.stego_image_path, model_path=self.model_path)
                
                if self.decode_use_decrypt.get() and CRYPTO_AVAILABLE:
                    with open(self.private_key_path, 'rb') as f:
                        private_key = RSA.import_key(f.read())
                    
                    import struct
                    data = bytes.fromhex(message)
                    enc_key_len = struct.unpack('<I', data[:4])[0]
                    enc_aes_key = data[4:4+enc_key_len]
                    iv = data[4+enc_key_len:4+enc_key_len+16]
                    ct = data[4+enc_key_len+16:]
                    
                    cipher_rsa = PKCS1_OAEP.new(private_key)
                    aes_key = cipher_rsa.decrypt(enc_aes_key)
                    
                    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
                    message = unpad(cipher_aes.decrypt(ct), AES.block_size).decode('utf-8')
                
                self.decode_text.delete('1.0', tk.END)
                self.decode_text.insert('1.0', message)
                
                end_ram = self.process.memory_info().rss / (1024 * 1024)  # MB
                elapsed_time = time.time() - start_time
                ram_used = end_ram - start_ram
                self.peak_ram_mb = max(self.peak_ram_mb, end_ram)
                
                status_msg = f"Decode thành công! | RAM: {ram_used:.1f}MB | Time: {elapsed_time:.2f}s"
                self.decode_status.config(text=status_msg, foreground='green')
                
                self.update_ram_info()
                
            except Exception as e:
                self.decode_status.config(text=f"Loi: {str(e)}", foreground='red')
                messagebox.showerror("Lỗi", f"Decode thất bại:\n{str(e)}")
        
        threading.Thread(target=decode_thread, daemon=True).start()
        
    def save_decoded(self):
        content = self.decode_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("Cảnh báo", "Không có nội dung để lưu!")
            return
            
        path = filedialog.asksaveasfilename(
            title="Lưu tin đã decode",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Thành công", f"Đã lưu vào:\n{path}")
            
    def select_reverse_stego(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh stego",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if path:
            self.reverse_stego_path = path
            self.reverse_stego_label.config(text=Path(path).name)
            
            try:
                img = Image.open(path)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                self.reverse_stego_preview.config(image=photo, text="")
                self.reverse_stego_preview.image = photo
            except:
                pass
                
    def run_reverse(self):
        if not hasattr(self, 'reverse_stego_path') or not self.reverse_stego_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh stego!")
            return
            
        output_path = filedialog.asksaveasfilename(
            title="Lưu ảnh đã khôi phục",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not output_path:
            return
            
        def reverse_thread():
            try:
                self.reverse_status.config(text="⏳ Đang reverse...", foreground='blue')
                self.root.update()
                
                # Gọi hàm reverse_hiding và kiểm tra kết quả
                result = reverse_hiding(self.reverse_stego_path, output_path, model_path=self.model_path)
                
                # Kiểm tra file đã được tạo thành công
                if not os.path.exists(output_path):
                    raise FileNotFoundError(f"File kết quả không được tạo: {output_path}")
                
                self.reversed_image_path = output_path
                
                # Load và hiển thị ảnh kết quả
                img = Image.open(output_path)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                self.reverse_recovered_preview.config(image=photo, text="")
                self.reverse_recovered_preview.image = photo
                
                # Cập nhật status
                self.reverse_status.config(text=f"✓ Đã lưu: {Path(output_path).name}", 
                                          foreground='green')
                
                # Hiển thị thông báo thành công
                self.root.after(0, lambda: messagebox.showinfo("Thành công", 
                    f"Đã khôi phục ảnh cover thành công!\n\nĐường dẫn: {output_path}"))
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                print(f"Lỗi reverse: {error_msg}")
                print(traceback.format_exc())
                self.reverse_status.config(text=f"✗ Lỗi: {error_msg}", foreground='red')
                self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Reverse thất bại:\n{error_msg}"))
        
        threading.Thread(target=reverse_thread, daemon=True).start()
        
    def save_reversed(self):
        if not hasattr(self, 'reversed_image_path') or not self.reversed_image_path:
            messagebox.showwarning("Cảnh báo", "Chưa có ảnh đã reverse!")
            return
            
        path = filedialog.asksaveasfilename(
            title="Lưu lại ảnh đã khôi phục",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if path:
            import shutil
            shutil.copy(self.reversed_image_path, path)
            messagebox.showinfo("Thành công", f"Đã lưu vào:\n{path}")
            
    def select_genrsa_dir(self):
        path = filedialog.askdirectory(title="Chọn thư mục lưu khóa")
        if path:
            self.genrsa_dir = path
            self.genrsa_dir_label.config(text=Path(path).name)
            
    def run_genrsa(self):
        if not self.genrsa_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu khóa!")
            return
            
        if not CRYPTO_AVAILABLE:
            messagebox.showerror("Lỗi", "Thư viện pycryptodome chưa được cài đặt!")
            return
            
        def genrsa_thread():
            try:
                self.genrsa_output.delete('1.0', tk.END)
                self.genrsa_output.insert('1.0', f"Đang tạo khóa RSA {self.key_size.get()} bits...\n")
                self.root.update()
                
                key = RSA.generate(self.key_size.get())
                private_key = key.export_key()
                public_key = key.publickey().export_key()
                
                public_path = Path(self.genrsa_dir) / "public_key.pem"
                private_path = Path(self.genrsa_dir) / "private_key.pem"
                
                with open(public_path, 'wb') as f:
                    f.write(public_key)
                with open(private_path, 'wb') as f:
                    f.write(private_key)
                
                self.genrsa_output.insert(tk.END, f"\nTạo khóa thành công!\n")
                self.genrsa_output.insert(tk.END, f"\nPublic key:\n{public_path}\n")
                self.genrsa_output.insert(tk.END, f"\nPrivate key:\n{private_path}\n")
                self.genrsa_output.insert(tk.END, f"\nLƯU Ý: Giữ private key an toàn!\n")
                
                self.genrsa_output.insert(tk.END, f"\n" + "="*60 + "\n")
                self.genrsa_output.insert(tk.END, "Public Key Content:\n")
                self.genrsa_output.insert(tk.END, "="*60 + "\n")
                self.genrsa_output.insert(tk.END, public_key.decode('utf-8'))
                
                messagebox.showinfo("Thành công", 
                                  f"Đã tạo cặp khóa RSA!\n\nPublic: {public_path}\nPrivate: {private_path}")
                
            except Exception as e:
                self.genrsa_output.insert(tk.END, f"\nLỗi: {str(e)}\n")
                messagebox.showerror("Lỗi", f"Tạo khóa thất bại:\n{str(e)}")
        
        threading.Thread(target=genrsa_thread, daemon=True).start()
        
    def setup_debug_tab(self):
        """Setup Debug tab"""
        frame = ttk.Frame(self.debug_tab, padding=20)
        frame.pack(fill='both', expand=True)
        
        title = ttk.Label(frame, text="Debug - Console Log", 
                         font=('Helvetica', 18, 'bold'))
        title.pack(pady=(0, 10))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="Refresh", 
                  command=self.refresh_debug_log).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Clear", 
                  command=self.clear_debug_log).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Save Log", 
                  command=self.save_debug_log).pack(side='left', padx=5)
        
        self.auto_refresh = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_frame, text="Auto-refresh", 
                       variable=self.auto_refresh).pack(side='left', padx=20)
        
        log_frame = ttk.LabelFrame(frame, text="Console Output", padding=10)
        log_frame.pack(fill='both', expand=True, pady=10)
        
        self.debug_log = scrolledtext.ScrolledText(log_frame, height=25, wrap=tk.WORD,
                                                    font=('Courier', 10))
        self.debug_log.pack(fill='both', expand=True)
        
        ram_frame = ttk.LabelFrame(frame, text="RAM Usage", padding=10)
        ram_frame.pack(fill='x', pady=5)
        
        self.ram_info_label = ttk.Label(ram_frame, text="Current RAM: N/A | Peak RAM: N/A", 
                                        font=('Courier', 10))
        self.ram_info_label.pack(pady=5)
        
        self.debug_status = ttk.Label(frame, text="Console logging active", foreground='green')
        self.debug_status.pack(pady=5)
        
        self.log_messages = []
        
    def setup_console_redirect(self):
        """Redirect stdout and stderr to capture console output"""
        import sys
        
        class ConsoleRedirect:
            def __init__(self, text_widget, original_stream, log_storage):
                self.text_widget = text_widget
                self.original_stream = original_stream
                self.log_storage = log_storage
                
            def write(self, message):
                self.log_storage.append(message)
                if hasattr(self, 'text_widget') and self.text_widget:
                    try:
                        self.text_widget.insert(tk.END, message)
                        self.text_widget.see(tk.END)
                    except:
                        pass
                # Check if original_stream exists (None when --windowed mode)
                if self.original_stream is not None:
                    try:
                        self.original_stream.write(message)
                        self.original_stream.flush()
                    except:
                        pass
                
            def flush(self):
                if self.original_stream is not None:
                    try:
                        self.original_stream.flush()
                    except:
                        pass
        
        sys.stdout = ConsoleRedirect(self.debug_log, sys.__stdout__, self.log_messages)
        sys.stderr = ConsoleRedirect(self.debug_log, sys.__stderr__, self.log_messages)
        
        self.auto_refresh_debug()
        
    def auto_refresh_debug(self):
        """Auto-refresh debug log every 1 second if enabled"""
        if self.auto_refresh.get():
            self.refresh_debug_log()
        self.root.after(1000, self.auto_refresh_debug)
        
    def refresh_debug_log(self):
        """Refresh the debug log display"""
        try:
            self.debug_log.see(tk.END)
            count = len(self.log_messages)
            self.debug_status.config(text=f"Console logging active - {count} messages", 
                                    foreground='green')
        except:
            pass
            
    def clear_debug_log(self):
        """Clear the debug log"""
        self.debug_log.delete('1.0', tk.END)
        self.log_messages.clear()
        self.debug_status.config(text="Log cleared", foreground='blue')
        
    def update_ram_info(self):
        """Update RAM usage information in Debug tab"""
        try:
            current_ram = self.process.memory_info().rss / (1024 * 1024)  # MB
            ram_info = f"Current RAM: {current_ram:.1f} MB | Peak RAM: {self.peak_ram_mb:.1f} MB"
            self.ram_info_label.config(text=ram_info)
        except Exception as e:
            self.ram_info_label.config(text=f"RAM monitoring error: {str(e)}")
    
    def save_debug_log(self):
        """Save debug log to file"""
        content = self.debug_log.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("Cảnh báo", "Không có log để lưu!")
            return
            
        from datetime import datetime
        default_name = f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        path = filedialog.asksaveasfilename(
            title="Lưu debug log",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Thành công", f"Đã lưu log vào:\n{path}")
    
    def select_compare_img1(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh 1 (Cover/Original)",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if path:
            self.compare_img1_path = path
            self.compare_img1_label.config(text=Path(path).name)
            
    def select_compare_img2(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh 2 (Stego/Recovered)",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if path:
            self.compare_img2_path = path
            self.compare_img2_label.config(text=Path(path).name)
            
    def run_compare(self):
        if not self.compare_img1_path or not self.compare_img2_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn cả 2 ảnh!")
            return
            
        def compare_thread():
            try:
                img1 = np.array(Image.open(self.compare_img1_path).convert('RGB'))
                img2 = np.array(Image.open(self.compare_img2_path).convert('RGB'))
                
                if img1.shape != img2.shape:
                    messagebox.showerror("Lỗi", 
                        f"Kích thước ảnh không khớp!\nẢnh 1: {img1.shape}\nẢnh 2: {img2.shape}")
                    return
                
                psnr_val = psnr(img1, img2)
                ssim_val = ssim(img1, img2, channel_axis=2, data_range=255)
                
                mse_val = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
                
                self.metrics_text.delete('1.0', tk.END)
                self.metrics_text.insert('1.0', "="*60 + "\n")
                self.metrics_text.insert(tk.END, "IMAGE QUALITY METRICS\n")
                self.metrics_text.insert(tk.END, "="*60 + "\n\n")
                
                self.metrics_text.insert(tk.END, f"Ảnh 1: {Path(self.compare_img1_path).name}\n")
                self.metrics_text.insert(tk.END, f"Ảnh 2: {Path(self.compare_img2_path).name}\n\n")
                
                self.metrics_text.insert(tk.END, f"Kích thước: {img1.shape[1]} x {img1.shape[0]}\n\n")
                
                self.metrics_text.insert(tk.END, "Metrics:\n")
                self.metrics_text.insert(tk.END, "-" * 60 + "\n")
                self.metrics_text.insert(tk.END, f"PSNR:  {psnr_val:>10.2f} dB\n")
                self.metrics_text.insert(tk.END, f"SSIM:  {ssim_val:>10.6f}\n")
                self.metrics_text.insert(tk.END, f"MSE:   {mse_val:>10.6f}\n")
                self.metrics_text.insert(tk.END, "-" * 60 + "\n\n")
                
                self.metrics_text.insert(tk.END, "Đánh giá:\n")
                self.metrics_text.insert(tk.END, "-" * 60 + "\n")
                
                if psnr_val > 40:
                    self.metrics_text.insert(tk.END, "PSNR > 40 dB: Chat luong rat tot\n")
                elif psnr_val > 30:
                    self.metrics_text.insert(tk.END, "  PSNR > 30 dB: Chat luong tot\n")
                else:
                    self.metrics_text.insert(tk.END, "  PSNR < 30 dB: Chat luong trung binh\n")
                    
                if ssim_val > 0.95:
                    self.metrics_text.insert(tk.END, "SSIM > 0.95: Tuong dong rat cao\n")
                elif ssim_val > 0.90:
                    self.metrics_text.insert(tk.END, "  SSIM > 0.90: Tuong dong cao\n")
                else:
                    self.metrics_text.insert(tk.END, "  SSIM < 0.90: Tuong dong trung binh\n")
                
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                
                fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                
                axes[0].imshow(img1)
                axes[0].set_title(f'Image 1\n{Path(self.compare_img1_path).name}', fontsize=10)
                axes[0].axis('off')
                
                axes[1].imshow(img2)
                axes[1].set_title(f'Image 2\n{Path(self.compare_img2_path).name}', fontsize=10)
                axes[1].axis('off')
                
                diff = np.abs(img1.astype(float) - img2.astype(float))
                diff_amp = (diff * 10).clip(0, 255).astype(np.uint8)
                axes[2].imshow(diff_amp)
                axes[2].set_title(f'Difference (10x)\nMax: {diff.max():.2f}', fontsize=10)
                axes[2].axis('off')
                
                plt.tight_layout()
                
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                plt.savefig(temp_file.name, dpi=100, bbox_inches='tight')
                plt.close()
                
                self.comparison_image = temp_file.name
                
                comp_img = Image.open(temp_file.name)
                comp_img.thumbnail((900, 300))
                photo = ImageTk.PhotoImage(comp_img)
                self.compare_preview.config(image=photo, text="")
                self.compare_preview.image = photo
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"So sánh thất bại:\n{str(e)}")
        
        threading.Thread(target=compare_thread, daemon=True).start()
        
    def save_comparison(self):
        if not self.comparison_image:
            messagebox.showwarning("Cảnh báo", "Chưa có ảnh comparison!")
            return
            
        path = filedialog.asksaveasfilename(
            title="Lưu ảnh comparison",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if path:
            import shutil
            shutil.copy(self.comparison_image, path)
            messagebox.showinfo("Thành công", f"Đã lưu vào:\n{path}")


def main():
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
