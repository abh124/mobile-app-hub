import flet as ft
import os
import threading
import re

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False


def get_yt_downloader_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for YouTube Video & Audio Downloader."""

    status_text = ft.Text("", size=13, weight=ft.FontWeight.W_500)
    progress_bar = ft.ProgressBar(value=0.0, visible=False, color=ft.Colors.RED_500)

    def set_status(msg: str, color=ft.Colors.GREEN_400):
        status_text.value = msg
        status_text.color = color
        page.update()

    url_input = ft.TextField(
        hint_text="Paste YouTube URL here (e.g. https://www.youtube.com/watch?v=...)",
        border_radius=12,
        expand=True,
        autofocus=True,
    )

    thumbnail_img = ft.Image(
        src="",
        width=260,
        height=146,
        fit="contain",
        visible=False,
        border_radius=12,
    )

    video_title_text = ft.Text("", size=15, weight=ft.FontWeight.BOLD, visible=False)
    video_channel_text = ft.Text("", size=13, color=ft.Colors.GREY_400, visible=False)

    download_mode = ft.Dropdown(
        label="Download Format",
        value="Video (MP4 - Best Quality)",
        options=[
            ft.dropdown.Option("Video (MP4 - Best Quality)"),
            ft.dropdown.Option("Video (MP4 - 720p)"),
            ft.dropdown.Option("Video (MP4 - 480p)"),
            ft.dropdown.Option("Audio Only (MP3 / Best Audio)"),
        ],
        border_radius=10,
        expand=True,
    )

    fetched_info = [None]
    download_btn = ft.Button("Download Now 🚀", icon=ft.Icons.DOWNLOAD_ROUNDED, disabled=True)

    def clean_ansi(text: str) -> str:
        return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)

    def fetch_video_info(_):
        url = url_input.value.strip()
        if not url:
            set_status("Please enter a valid YouTube URL!", ft.Colors.AMBER_400)
            return

        if not HAS_YTDLP:
            set_status("yt-dlp library is not installed!", ft.Colors.RED_400)
            return

        set_status("Fetching video metadata...", ft.Colors.BLUE_400)
        progress_bar.visible = True
        progress_bar.value = None  # Indeterminate loading
        page.update()

        def _worker():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    fetched_info[0] = info

                title = info.get("title", "YouTube Video")
                uploader = info.get("uploader", "Unknown Channel")
                thumb = info.get("thumbnail", "")

                video_title_text.value = title
                video_title_text.visible = True
                video_channel_text.value = f"Channel: {uploader}"
                video_channel_text.visible = True

                if thumb:
                    thumbnail_img.src = thumb
                    thumbnail_img.visible = True

                download_btn.disabled = False
                set_status("Ready to download! Select format below.", ft.Colors.GREEN_400)
            except Exception as ex:
                set_status(f"Error fetching URL: {ex}", ft.Colors.RED_400)
                download_btn.disabled = True
            finally:
                progress_bar.visible = False
                page.update()

        threading.Thread(target=_worker, daemon=True).start()

    def start_download(_):
        url = url_input.value.strip()
        if not url or not fetched_info[0]:
            set_status("Please fetch video details first!", ft.Colors.AMBER_400)
            return

        mode = download_mode.value

        def _download_thread():
            try:
                # Default save path: User's Downloads folder
                downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                if not os.path.exists(downloads_dir):
                    downloads_dir = os.getcwd()

                progress_bar.visible = True
                progress_bar.value = 0.0
                set_status("Starting download...", ft.Colors.BLUE_400)
                page.update()

                def progress_hook(d):
                    if d['status'] == 'downloading':
                        raw_perc = d.get('_percent_str', '0%')
                        clean_perc = clean_ansi(raw_perc).replace('%', '').strip()
                        try:
                            val = float(clean_perc) / 100.0
                            progress_bar.value = min(1.0, max(0.0, val))
                        except ValueError:
                            pass

                        speed = clean_ansi(d.get('_speed_str', 'N/A'))
                        eta = clean_ansi(d.get('_eta_str', 'N/A'))
                        status_text.value = f"Downloading: {clean_perc}% ({speed}, ETA: {eta})"
                        status_text.color = ft.Colors.BLUE_400
                        page.update()

                    elif d['status'] == 'finished':
                        progress_bar.value = 1.0
                        set_status("Processing file...", ft.Colors.AMBER_400)

                out_tmpl = os.path.join(downloads_dir, "%(title)s.%(ext)s")

                if "Audio Only" in mode:
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': out_tmpl,
                        'progress_hooks': [progress_hook],
                        'quiet': True,
                        'no_warnings': True,
                    }
                elif "720p" in mode:
                    ydl_opts = {
                        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best',
                        'outtmpl': out_tmpl,
                        'progress_hooks': [progress_hook],
                        'quiet': True,
                        'no_warnings': True,
                    }
                elif "480p" in mode:
                    ydl_opts = {
                        'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best',
                        'outtmpl': out_tmpl,
                        'progress_hooks': [progress_hook],
                        'quiet': True,
                        'no_warnings': True,
                    }
                else:
                    # Best Quality
                    ydl_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': out_tmpl,
                        'progress_hooks': [progress_hook],
                        'quiet': True,
                        'no_warnings': True,
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                title = fetched_info[0].get("title", "Video")
                set_status(f"🎉 Download Complete! Saved to Downloads: '{title}'", ft.Colors.GREEN_400)
            except Exception as ex:
                set_status(f"Download error: {ex}", ft.Colors.RED_400)
            finally:
                progress_bar.visible = False
                page.update()

        threading.Thread(target=_download_thread, daemon=True).start()

    download_btn.on_click = start_download

    return ft.Column([
        ft.Text("YouTube Video & Audio Downloader 🎬", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("Paste any YouTube video or shorts link to download Video or MP3 Audio.", size=12, color=ft.Colors.GREY_400),
        ft.Row([
            url_input,
            ft.Button("Fetch Info 🔍", on_click=fetch_video_info, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)),
        ]),
        status_text,
        progress_bar,
        ft.Container(
            content=ft.Column([
                thumbnail_img,
                video_title_text,
                video_channel_text,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=10,
        ),
        ft.Row([download_mode]),
        ft.Container(
            content=download_btn,
            alignment=ft.Alignment.CENTER,
            padding=10,
        ),
        ft.Divider(),
        ft.Text("Features:", size=13, color=ft.Colors.GREY_400),
        ft.Text("• Downloads MP4 Video (1080p, 720p, 480p) & Audio\n• Live percentage & speed progress updates\n• Automatic saving directly to your Downloads folder", size=12, color=ft.Colors.GREY_500),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
