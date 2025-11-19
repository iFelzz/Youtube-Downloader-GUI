import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import threading
import shutil
from urllib.parse import urlparse
import logging
import re
import importlib
try:
    yt_dlp = importlib.import_module("yt_dlp")
    HAS_YTDLP = True
except Exception:
    yt_dlp = None
    HAS_YTDLP = False

# Setup basic logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('ytdl_gui.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

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
def download(url, output_folder, mode, height=None, ui_app=None, done_callback=None):
    # Prefer Python API of yt_dlp if available
    if HAS_YTDLP:
        # Prepare format
        if mode == "mp3":
            fmt = "bestaudio/best"
        else:
            if height:
                fmt = f"bestvideo[height={height}]+bestaudio/best"
            else:
                fmt = "bestvideo+bestaudio/best"

        outtmpl = os.path.join(output_folder, "%(title)s.%(ext)s")

        def progress_hook(d):
            status = d.get("status")
            if status == "downloading":
                downloaded = d.get("downloaded_bytes")
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                speed = d.get("speed")
                if downloaded and total:
                    try:
                        perc = downloaded / total * 100.0
                    except Exception:
                        perc = None
                    if perc is not None and ui_app and hasattr(ui_app, "root"):
                        def _set_val(p=perc, s=speed):
                            try:
                                # Switch to determinate on first progress
                                ui_app.download_progress.config(mode='determinate', maximum=100)
                                ui_app.download_progress['value'] = p
                                # Update percent label
                                try:
                                    if hasattr(ui_app, '_progress_pct_label') and ui_app._progress_pct_label:
                                        ui_app._progress_pct_label.config(text=f"{p:.1f}%")
                                except Exception:
                                    logging.exception("Gagal update label persen")
                                # Update speed label
                                try:
                                    txt = ''
                                    if s:
                                        try:
                                            ss = float(s)
                                        except Exception:
                                            ss = None
                                        if ss is not None:
                                            units = ['B/s','KiB/s','MiB/s','GiB/s']
                                            i = 0
                                            while ss >= 1024 and i < len(units)-1:
                                                ss /= 1024.0
                                                i += 1
                                            txt = f"{ss:.2f} {units[i]}"
                                        else:
                                            txt = str(s)
                                    if hasattr(ui_app, '_progress_speed_label') and ui_app._progress_speed_label:
                                        ui_app._progress_speed_label.config(text=txt)
                                except Exception:
                                    logging.exception("Gagal update label speed")
                            except Exception:
                                logging.exception("Gagal update progress via API")
                        ui_app.root.after(0, _set_val)
                # cancellation
                if ui_app and getattr(ui_app, '_download_cancelled', False):
                    raise Exception("Download dibatalkan oleh pengguna")
            # saat selesai, biarkan done_callback/on_download_finished yang menampilkan notifikasi
            elif status == "finished":
                pass

        ydl_opts = {
            'format': fmt,
            'outtmpl': outtmpl,
            'noplaylist': True,
            'progress_hooks': [progress_hook],
        }
        if mode == "mp3":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            rc = 0
        except Exception as e:
            logging.exception("Error saat menggunakan yt_dlp API")
            rc = 1
            if ui_app and hasattr(ui_app, "root"):
                ui_app.root.after(0, lambda: messagebox.showerror("Error", f"Download gagal: {e}"))

        # Call done
        if done_callback and ui_app and hasattr(ui_app, "root"):
            ui_app.root.after(0, done_callback)
        return

    # Fallback: use external yt-dlp executable and parse stdout
    # Pastikan yt-dlp tersedia
    if shutil.which("yt-dlp") is None:
        if ui_app and hasattr(ui_app, "root"):
            ui_app.root.after(0, lambda: messagebox.showerror("Error", "yt-dlp tidak ditemukan. Silakan instal yt-dlp terlebih dahulu."))
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

    # Gunakan Popen untuk membaca output progress secara real-time
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        # Simpan handle proses ke app agar bisa dibatalkan
        if ui_app is not None:
            try:
                ui_app._download_proc = proc
            except Exception:
                logging.exception("Gagal menyimpan handle proses ke ui_app")
    except FileNotFoundError as e:
        logging.exception("yt-dlp tidak dapat dijalankan")
        if ui_app and hasattr(ui_app, "root"):
            ui_app.root.after(0, lambda: messagebox.showerror("Error", f"Gagal menjalankan yt-dlp:\n{e}"))
            if done_callback:
                ui_app.root.after(0, done_callback)
        return

    perc_re = re.compile(r"(\d{1,3}(?:\.\d+)?)%")
    # capture speed like 'at 123.45KiB/s' (common yt-dlp output)
    speed_re = re.compile(r"at\s*([0-9]+(?:\.[0-9]+)?(?:[KkMmGg]i?B/s|B/s))")
    saw_percent = False
    try:
        # Baca baris demi baris
        for raw in proc.stdout:
            line = raw.strip()
            logging.debug("yt-dlp: %s", line)
            m = perc_re.search(line)
            if m:
                try:
                    perc = float(m.group(1))
                except Exception:
                    continue
                # On first percent, switch download_progress to determinate
                if not saw_percent:
                    saw_percent = True
                    if ui_app and hasattr(ui_app, "root"):
                        def _switch_to_determinate(p=perc):
                            try:
                                try:
                                    ui_app.download_progress.stop()
                                except Exception:
                                    pass
                                ui_app.download_progress.config(mode='determinate', maximum=100)
                                ui_app.download_progress['value'] = p
                                # update percent label
                                try:
                                    if hasattr(ui_app, '_progress_pct_label') and ui_app._progress_pct_label:
                                        ui_app._progress_pct_label.config(text=f"{p:.1f}%")
                                except Exception:
                                    logging.exception("Gagal update label persen")
                                # update speed label if available
                                try:
                                    sm = speed_re.search(line)
                                    sp_txt = sm.group(1) if sm else ''
                                    if hasattr(ui_app, '_progress_speed_label') and ui_app._progress_speed_label:
                                        ui_app._progress_speed_label.config(text=sp_txt)
                                except Exception:
                                    logging.exception("Gagal update label speed")
                            except Exception:
                                logging.exception("Gagal beralih ke determinate")
                        ui_app.root.after(0, _switch_to_determinate)
                else:
                    # update value
                    if ui_app and hasattr(ui_app, "root"):
                        def _set_val(p=perc):
                            try:
                                ui_app.download_progress['value'] = p
                                try:
                                    if hasattr(ui_app, '_progress_pct_label') and ui_app._progress_pct_label:
                                        ui_app._progress_pct_label.config(text=f"{p:.1f}%")
                                except Exception:
                                    logging.exception("Gagal update label persen")
                                try:
                                    sm = speed_re.search(line)
                                    sp_txt = sm.group(1) if sm else ''
                                    if hasattr(ui_app, '_progress_speed_label') and ui_app._progress_speed_label:
                                        ui_app._progress_speed_label.config(text=sp_txt)
                                except Exception:
                                    logging.exception("Gagal update label speed")
                            except Exception:
                                logging.exception("Gagal update progress bar")
                        ui_app.root.after(0, _set_val)
        rc = proc.wait()
    except Exception:
        logging.exception("Error saat membaca output yt-dlp")
        proc.kill()
        rc = proc.wait()

    # Clear stored process handle
    try:
        if ui_app is not None:
            ui_app._download_proc = None
    except Exception:
        logging.exception("Gagal menghapus handle proses dari ui_app")

    if rc != 0:
        err_msg = f"yt-dlp exited with code {rc}"
        logging.error(err_msg)
        if ui_app and hasattr(ui_app, "root"):
            ui_app.root.after(0, lambda: messagebox.showerror("Error", err_msg))
    else:
        if ui_app and hasattr(ui_app, "root"):
            # Jika tidak melihat persentase, biarkan done_callback menampilkan notifikasi di pop-up
            pass

    # Panggil callback selesai untuk mengembalikan UI ke keadaan normal
    if done_callback and ui_app and hasattr(ui_app, "root"):
        ui_app.root.after(0, done_callback)

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
        self._download_proc = None
        self._download_cancelled = False

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

        # Frame untuk resolusi MP4 (judul ditempatkan di tengah atas)
        self.res_frame = tk.LabelFrame(root, text="Pilih Resolusi (MP4 Only)", labelanchor='n')
        self.res_frame.pack(pady=10, fill="both", expand=True)

        # Progressbar loading
        self.progress = ttk.Progressbar(self.res_frame, mode="indeterminate")
        # Progressbar untuk download (dibuat di pop-up saat download dimulai)
        self.download_progress = None
        self._progress_win = None
        self._progress_cancel_btn = None

        # Download button container (Cancel/Open Folder removed from main window)
        btn_frame = tk.Frame(root)
        btn_frame.pack(side="bottom", pady=10)

        self.download_button = tk.Button(btn_frame, text="Download", command=self.start_download)
        self.download_button.pack(side="left", padx=5)

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
        # Jika ada label 'no format', hancurkan juga saat beralih mode
        if hasattr(self, "_no_format_label") and self._no_format_label:
            try:
                self._no_format_label.destroy()
            except Exception:
                pass
            self._no_format_label = None

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

        # Nonaktifkan tombol utama dan tampilkan pop-up progress
        self.download_button.config(state=tk.DISABLED)
        self._download_cancelled = False

        # Buat pop-up progress
        try:
            self._progress_win = tk.Toplevel(self.root)
            self._progress_win.title("Downloading...")
            self._progress_win.transient(self.root)
            self._progress_win.grab_set()
            # Label status
            lbl = tk.Label(self._progress_win, text="Mengunduh, tunggu...")
            lbl.pack(padx=12, pady=(12, 6))
            # Progressbar di pop-up
            self.download_progress = ttk.Progressbar(self._progress_win, mode='indeterminate', length=400)
            self.download_progress.pack(padx=12, pady=6, fill='x')
            try:
                self.download_progress.start()
            except Exception:
                pass
            # Percentage and speed labels (will be updated during download)
            self._progress_pct_label = tk.Label(self._progress_win, text="0%")
            self._progress_pct_label.pack(padx=12, pady=(0, 2))
            self._progress_speed_label = tk.Label(self._progress_win, text="")
            self._progress_speed_label.pack(padx=12, pady=(0, 6))
            # Tombol Cancel ada di pop-up
            self._progress_cancel_btn = tk.Button(self._progress_win, text="Cancel", command=self.cancel_download)
            self._progress_cancel_btn.pack(pady=(6, 12))
            # Disable menutup window manual agar kontrol lewat tombol
            self._progress_win.protocol("WM_DELETE_WINDOW", lambda: None)
            # Posisikan pop-up di tengah jendela utama
            try:
                self._progress_win.update_idletasks()
                win_w = self._progress_win.winfo_width()
                win_h = self._progress_win.winfo_height()
                root_x = self.root.winfo_rootx()
                root_y = self.root.winfo_rooty()
                root_w = self.root.winfo_width()
                root_h = self.root.winfo_height()
                x = root_x + max(0, (root_w - win_w) // 2)
                y = root_y + max(0, (root_h - win_h) // 2)
                self._progress_win.geometry(f"+{x}+{y}")
            except Exception:
                logging.exception("Gagal memposisikan pop-up di tengah")
        except Exception:
            logging.exception("Gagal membuat pop-up progress")

        # Start download thread; download will set app._download_proc to the subprocess
        threading.Thread(target=download, args=(url, folder, mode, height, self, self.on_download_finished), daemon=True).start()

    def on_download_finished(self):
        try:
            # Reset download process handle
            try:
                self._download_proc = None
            except Exception:
                pass

            # Jika ada pop-up progress, ubah tampilannya menjadi notifikasi selesai / dibatalkan
            if hasattr(self, '_progress_win') and self._progress_win:
                try:
                    # Hentikan progressbar jika ada
                    try:
                        if self.download_progress:
                            self.download_progress.stop()
                    except Exception:
                        pass

                    # Hapus semua widget di dalam progress window
                    for child in list(self._progress_win.winfo_children()):
                        try:
                            child.destroy()
                        except Exception:
                            pass

                    # Tampilkan pesan sesuai keadaan
                    if getattr(self, '_download_cancelled', False):
                        msg = "Download dibatalkan."
                    else:
                        msg = "Download selesai!"
                    lbl = tk.Label(self._progress_win, text=msg)
                    lbl.pack(padx=12, pady=(12, 8))

                    # Tombol-tombol: Open Folder (jika berhasil) dan OK untuk tutup
                    btn_frame = tk.Frame(self._progress_win)
                    btn_frame.pack(pady=(6, 12))

                    ok_btn = tk.Button(btn_frame, text="OK", width=10, command=lambda: self._close_progress_popup())
                    ok_btn.pack(side='left', padx=6)

                    # Hanya aktifkan Open Folder bila folder valid dan bukan cancelled
                    try:
                        folder = self.output_folder.get()
                        if folder and os.path.isdir(folder) and not getattr(self, '_download_cancelled', False):
                            open_btn = tk.Button(btn_frame, text="Open Folder", width=12, command=self.open_folder)
                            open_btn.pack(side='left', padx=6)
                    except Exception:
                        logging.exception("Gagal membuat tombol Open Folder di pop-up")

                    # Biarkan pengguna menutup pop-up sendiri via OK; lepaskan grab
                    try:
                        self._progress_win.grab_release()
                    except Exception:
                        pass
                    # Pastikan cancel button ref dihapus
                    self._progress_cancel_btn = None
                except Exception:
                    logging.exception("Gagal memperbarui pop-up setelah download selesai")

            # Kembalikan UI utama
            self.download_button.config(state=tk.NORMAL)
            try:
                # If output folder valid, nothing to enable in main window (Open Folder removed)
                pass
            except Exception:
                pass
        except Exception:
            logging.exception("Error saat mengembalikan UI setelah download selesai")

    def _close_progress_popup(self):
        try:
            if hasattr(self, '_progress_win') and self._progress_win:
                try:
                    self._progress_win.destroy()
                except Exception:
                    pass
                self._progress_win = None
            # Clear download_progress reference
            try:
                self.download_progress = None
            except Exception:
                pass
        except Exception:
            logging.exception("Error saat menutup progress popup")

    def cancel_download(self):
        # Set cancel flag for yt_dlp API path; kill subprocess if present
        self._download_cancelled = True
        proc = getattr(self, '_download_proc', None)
        if proc:
            try:
                proc.kill()
                logging.info('Download process killed by user')
            except Exception:
                logging.exception('Gagal membunuh proses download')
        # Ensure UI returns to normal
        try:
            self.on_download_finished()
        except Exception:
            logging.exception('Error saat membatalkan download')

    def open_folder(self):
        folder = self.output_folder.get()
        if folder and os.path.isdir(folder):
            try:
                if os.name == 'nt':
                    os.startfile(folder)
                else:
                    subprocess.run(['xdg-open', folder])
            except Exception:
                logging.exception('Gagal membuka folder')


# ===============================
# Jalankan GUI
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
