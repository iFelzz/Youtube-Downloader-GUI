import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import threading

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
        messagebox.showerror("Error", f"Gagal mengambil format video:\n{e}")
        callback([])

# ===============================
# Fungsi download
# ===============================
def download(url, output_folder, mode, height=None):
    if mode == "mp3":
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", os.path.join(output_folder, "%(title)s.%(ext)s"), url]
    else:  # mp4
        if height:
            fmt = f"bestvideo[height={height}]+bestaudio/best"
        else:
            fmt = "bestvideo+bestaudio/best"
        cmd = ["yt-dlp", "-f", fmt, "-o", os.path.join(output_folder, "%(title)s.%(ext)s"), url]

    subprocess.run(cmd)
    messagebox.showinfo("Selesai", "Download selesai!")

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

        # URL
        tk.Label(root, text="URL YouTube:").pack(pady=5)
        tk.Entry(root, textvariable=self.url, width=60).pack(pady=5)

        # Folder
        tk.Button(root, text="Pilih Folder Output", command=self.choose_folder).pack(pady=5)
        tk.Label(root, textvariable=self.output_folder, fg="blue").pack(pady=5)

        # Mode radio button
        tk.Label(root, text="Pilih Mode Download:").pack(pady=5)
        tk.Radiobutton(root, text="MP3 (Audio)", variable=self.mode, value="mp3", command=self.mode_changed).pack()
        tk.Radiobutton(root, text="MP4 (Video)", variable=self.mode, value="mp4", command=self.mode_changed).pack()

        # Frame untuk resolusi MP4
        self.res_frame = tk.LabelFrame(root, text="Pilih Resolusi (MP4 Only)")
        self.res_frame.pack(pady=10)
        self.res_buttons = []

        # Label loading
        self.loading_label = tk.Label(self.res_frame, text="Loading...", fg="red")
        
        # Download button
        self.download_button = tk.Button(root, text="Download", command=self.start_download)
        self.download_button.pack(pady=10)

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
        self.loading_label.pack_forget()

        if self.mode.get() == "mp4":
            url = self.url.get().strip()
            if url:
                self.loading_label.pack()
                # Jalankan deteksi format di thread terpisah supaya GUI tidak nge-lag
                threading.Thread(target=get_video_formats, args=(url, self.populate_resolutions), daemon=True).start()

    def populate_resolutions(self, heights):
        # hapus loading label
        self.loading_label.pack_forget()

        if heights:
            for h in heights:
                btn = tk.Radiobutton(self.res_frame, text=f"{h}p", variable=self.resolution, value=h)
                btn.pack(anchor="w")
                self.res_buttons.append(btn)
            # Resize window otomatis sesuai jumlah resolusi
            self.root.update()
            self.root.geometry(f"{self.root.winfo_width()}x{self.res_frame.winfo_y() + self.res_frame.winfo_height() + 70}")
        else:
            tk.Label(self.res_frame, text="Tidak ada format video MP4 tersedia").pack()

    def start_download(self):
        url = self.url.get().strip()
        folder = self.output_folder.get().strip()
        mode = self.mode.get()
        height = self.resolution.get() if mode == "mp4" else None

        if not url:
            messagebox.showwarning("Peringatan", "Masukkan URL YouTube!")
            return
        if not folder:
            messagebox.showwarning("Peringatan", "Pilih folder output!")
            return
        if mode == "mp4" and not height:
            messagebox.showwarning("Peringatan", "Pilih resolusi video!")
            return

        threading.Thread(target=download, args=(url, folder, mode, height), daemon=True).start()

# ===============================
# Jalankan GUI
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
