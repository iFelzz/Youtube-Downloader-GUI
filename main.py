import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import threading
import shutil
from urllib.parse import urlparse
import logging

# ===============================
# Fungsi untuk ambil format video
# ===============================
def get_video_formats(url, callback):
    try:
        result = subprocess.run(
            ["yt-dlp", "-J", url],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)
        formats = data.get("formats", [])
        video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("ext") == "mp4"]
        heights = sorted(set(f.get("height") for f in video_formats if f.get("height") is not None))
        callback(heights)
    except Exception as e:
        logging.exception("Gagal mengambil format video")
        # Jangan panggil GUI dari thread worker; cukup laporkan kosong ke callback
        callback([])

# ===============================
# Fungsi download
# ===============================
def download(url, output_folder, mode, height=None, ui_root=None, done_callback=None):
    # Pastikan yt-dlp tersedia
    if shutil.which("yt-dlp") is None:
        if ui_root:
            ui_root.after(0, lambda: messagebox.showerror("Error", "yt-dlp tidak ditemukan. Silakan instal yt-dlp terlebih dahulu."))
        return

    if mode == "mp3":
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3",
               "-o", os.path.join(output_folder, "%(title)s.%(ext)s"), url]
    else:  # mp4
        if height:
            fmt = f"bestvideo[height={height}]+bestaudio/best"
        else:
            fmt = "bestvideo+bestaudio/best"
        cmd = ["yt-dlp", "-f", fmt,
               "-o", os.path.join(output_folder, "%(title)s.%(ext)s"), url]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as e:
        logging.exception("yt-dlp tidak dapat dijalankan")
        if ui_root:
            ui_root.after(0, lambda: messagebox.showerror("Error", f"Gagal menjalankan yt-dlp:\n{e}"))
        if done_callback and ui_root:
            ui_root.after(0, done_callback)
        return

    if result.returncode != 0:
        err = result.stderr or result.stdout or "Unknown error"
        logging.error("yt-dlp error: %s", err)
        if ui_root:
            ui_root.after(0, lambda: messagebox.showerror("Error", f"Download gagal:\n{err}"))
    else:
        if ui_root:
            ui_root.after(0, lambda: messagebox.showinfo("Selesai", "Download selesai!"))

    # Panggil callback selesai untuk mengembalikan UI ke keadaan normal
    if done_callback and ui_root:
        ui_root.after(0, done_callback)

# ===============================
# GUI
# ===============================
class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader GUI")
        self.root.geometry("500x400")

        self.url = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.mode = tk.StringVar(value="mp3")
        self.resolution = tk.IntVar(value=0)
        self.res_buttons = []
        self._no_format_label = None

        # URL
        tk.Label(root, text="URL YouTube:").pack(pady=5)
        self.url_entry = tk.Entry(root, textvariable=self.url, width=60, fg="grey")
        self.url_entry.insert(0, "Masukkan URL YouTube di sini...")
        self.url_entry.pack(pady=5)

        # Placeholder behavior
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.add_placeholder)


        # Folder
        tk.Button(root, text="Pilih Folder Output", command=self.choose_folder).pack(pady=5)
        tk.Label(root, textvariable=self.output_folder, fg="blue").pack(pady=5)

        # Mode radio button
        tk.Label(root, text="Pilih Mode Download:").pack(pady=5)
        tk.Radiobutton(root, text="MP3 (Audio)", variable=self.mode, value="mp3", command=self.mode_changed).pack()
        tk.Radiobutton(root, text="MP4 (Video)", variable=self.mode, value="mp4", command=self.mode_changed).pack()

        # Frame untuk resolusi MP4
        self.res_frame = tk.LabelFrame(root, text="Pilih Resolusi (MP4 Only)")
        self.res_frame.pack(pady=10, fill="both", expand=True)

        # Progressbar loading
        self.progress = ttk.Progressbar(self.res_frame, mode="indeterminate")
        # Progressbar untuk download
        self.download_progress = ttk.Progressbar(root, mode="indeterminate")

        # Download button
        self.download_button = tk.Button(root, text="Download", command=self.start_download)
        self.download_button.pack(side="bottom", pady=10)

    def clear_placeholder(self, event):
        if self.url_entry.get() == "Masukkan URL YouTube di sini...":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg="black")

    def add_placeholder(self, event):
        if not self.url_entry.get():
            self.url_entry.insert(0, "Masukkan URL YouTube di sini...")
            self.url_entry.config(fg="grey")

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def mode_changed(self):
        # Clear resolusi frame
        for btn in self.res_buttons:
            btn.destroy()
        self.res_buttons.clear()
        self.resolution.set(0)
        try:
            self.progress.grid_forget()
        except Exception:
            pass

        if self.mode.get() == "mp4":
            url = self.url.get().strip()
            if url:
                # Pastikan yt-dlp tersedia sebelum mengambil format
                if shutil.which("yt-dlp") is None:
                    messagebox.showerror("Error", "yt-dlp tidak ditemukan. Silakan instal yt-dlp terlebih dahulu.")
                    return
                self.progress.grid(row=0, column=0, columnspan=2, pady=5, sticky="we")
                self.progress.start()
                threading.Thread(target=self.fetch_formats_thread, args=(url,), daemon=True).start()

    def fetch_formats_thread(self, url):
        get_video_formats(url, lambda heights: self.root.after(0, self.populate_resolutions, heights))

    def populate_resolutions(self, heights):
        # Stop dan hide progress
        self.progress.stop()
        try:
            self.progress.grid_forget()
        except Exception:
            pass

        # Hapus radio button lama dan label pesan (jangan hancurkan progressbar)
        for btn in list(self.res_buttons):
            try:
                btn.destroy()
            except Exception:
                pass
        self.res_buttons.clear()
        if hasattr(self, "_no_format_label") and self._no_format_label:
            try:
                self._no_format_label.destroy()
            except Exception:
                pass
            self._no_format_label = None

        if heights:
            # Tampilkan radio button dalam dua kolom agar memanfaatkan ruang horizontal
            cols = 2
            for idx, h in enumerate(heights):
                row = (idx // cols) + 1
                col = idx % cols
                btn = tk.Radiobutton(self.res_frame, text=f"{h}p", variable=self.resolution, value=h)
                btn.grid(row=row, column=col, sticky="w", padx=10, pady=2)
                self.res_buttons.append(btn)
            # Buat kolom agar melebar merata
            for c in range(cols):
                self.res_frame.columnconfigure(c, weight=1)
        else:
            self._no_format_label = tk.Label(self.res_frame, text="Tidak ada format video MP4 tersedia")
            self._no_format_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

    def start_download(self):
        url = self.url.get().strip()
        folder = self.output_folder.get().strip()
        mode = self.mode.get()
        height = self.resolution.get() if mode == "mp4" else None

        if not url or url == "Masukkan URL YouTube di sini...":
            messagebox.showwarning("Peringatan", "Masukkan URL YouTube!")
            return
        # Validasi sederhana URL
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            messagebox.showwarning("Peringatan", "URL tidak valid. Gunakan http:// atau https://")
            return
        if not folder:
            messagebox.showwarning("Peringatan", "Pilih folder output!")
            return
        if not os.path.isdir(folder):
            messagebox.showwarning("Peringatan", "Folder output tidak ditemukan atau tidak valid!")
            return
        if not os.access(folder, os.W_OK):
            messagebox.showwarning("Peringatan", "Folder output tidak dapat ditulisi!")
            return
        if mode == "mp4" and not height:
            messagebox.showwarning("Peringatan", "Pilih resolusi video!")
            return

        # Nonaktifkan tombol dan tampilkan progress
        self.download_button.config(state=tk.DISABLED)
        self.download_progress.pack(pady=5)
        self.download_progress.start()

        threading.Thread(target=download, args=(url, folder, mode, height, self.root, self.on_download_finished), daemon=True).start()

    def on_download_finished(self):
        try:
            self.download_progress.stop()
            self.download_progress.pack_forget()
            self.download_button.config(state=tk.NORMAL)
        except Exception:
            logging.exception("Error saat mengembalikan UI setelah download selesai")


# ===============================
# Jalankan GUI
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
