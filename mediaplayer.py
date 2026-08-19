import flet as ft
import os
import threading
import webbrowser


def get_media_player_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for the Media Player (Audio & Video Playback)."""

    status_text = ft.Text("No media loaded.", size=13, color=ft.Colors.GREY_400)
    track_title = ft.Text("Select an Audio or Video file", size=16, weight=ft.FontWeight.BOLD, max_lines=1)
    track_subtitle = ft.Text("Supports MP3, WAV, M4A, MP4, AAC & Web URLs", size=12, color=ft.Colors.GREY_400)

    playlist = []
    current_idx = [-1]

    def set_status(msg: str, color=ft.Colors.GREEN_400):
        status_text.value = msg
        status_text.color = color
        page.update()

    def launch_media(src_path: str, title: str):
        try:
            track_title.value = title
            track_subtitle.value = f"File: {os.path.basename(src_path)}"

            if src_path.startswith("http://") or src_path.startswith("https://"):
                page.launch_url(src_path)
            else:
                if os.name == 'nt' and os.path.exists(src_path):
                    os.startfile(src_path)
                else:
                    webbrowser.open(src_path)

            set_status(f"▶ Playing: {title}", ft.Colors.GREEN_400)
        except Exception as ex:
            set_status(f"Error launching media: {ex}", ft.Colors.RED_400)
        page.update()

    playlist_column = ft.Column(spacing=6)

    def refresh_playlist_ui():
        playlist_column.controls.clear()
        if not playlist:
            playlist_column.controls.append(ft.Text("Playlist is empty. Click 'Add Media File' below.", size=12, color=ft.Colors.GREY_500))
        else:
            for idx, item in enumerate(playlist):
                def make_play(i):
                    return lambda _: play_track_index(i)

                is_curr = (idx == current_idx[0])
                playlist_column.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.INDIGO_900 if is_curr else ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=10,
                        border_radius=10,
                        content=ft.Row([
                            ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED if not is_curr else ft.Icons.PLAY_ARROW_ROUNDED, color=ft.Colors.GREEN_400 if is_curr else ft.Colors.WHITE, size=20),
                            ft.Text(item["title"], expand=True, size=13, weight=ft.FontWeight.BOLD if is_curr else ft.FontWeight.NORMAL),
                            ft.IconButton(icon=ft.Icons.PLAY_ARROW_ROUNDED, icon_size=20, icon_color=ft.Colors.GREEN_400, on_click=make_play(idx)),
                        ]),
                    )
                )
        page.update()

    def play_track_index(idx: int):
        if 0 <= idx < len(playlist):
            current_idx[0] = idx
            item = playlist[idx]
            launch_media(item["path"], item["title"])
            refresh_playlist_ui()

    def pick_media_file(_):
        def _open():
            try:
                from tkinter import Tk, filedialog
                root = Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                fpath = filedialog.askopenfilename(
                    title="Select Audio or Video File",
                    filetypes=[
                        ("Media Files", "*.mp3 *.wav *.m4a *.aac *.ogg *.mp4 *.mkv *.webm"),
                        ("Audio Files", "*.mp3 *.wav *.m4a *.aac *.ogg"),
                        ("Video Files", "*.mp4 *.mkv *.webm"),
                        ("All Files", "*.*"),
                    ]
                )
                root.destroy()
                if fpath and os.path.exists(fpath):
                    t_title = os.path.basename(fpath)
                    playlist.append({"title": t_title, "path": fpath})
                    current_idx[0] = len(playlist) - 1
                    launch_media(fpath, t_title)
                    refresh_playlist_ui()
            except Exception as ex:
                set_status(f"File picker error: {ex}", ft.Colors.RED_400)

        threading.Thread(target=_open, daemon=True).start()

    url_input = ft.TextField(hint_text="Or paste direct Audio/Video URL...", border_radius=10, expand=True)

    def load_from_url(_):
        u = url_input.value.strip()
        if u:
            t_title = os.path.basename(u) or "Web Stream"
            playlist.append({"title": t_title, "path": u})
            current_idx[0] = len(playlist) - 1
            launch_media(u, t_title)
            refresh_playlist_ui()
            url_input.value = ""

    play_current_btn = ft.Button(
        "Play Selected Track ▶",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        on_click=lambda _: play_track_index(current_idx[0]) if current_idx[0] >= 0 else set_status("Select a track first!", ft.Colors.AMBER_400),
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)),
    )

    return ft.Column([
        ft.Text("Media Player 🎵", size=18, weight=ft.FontWeight.BOLD),
        status_text,

        # Album Art & Banner Visualizer
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.MUSIC_VIDEO_ROUNDED, size=64, color=ft.Colors.INDIGO_400),
                track_title,
                track_subtitle,
                ft.Container(height=6),
                play_current_btn,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=20,
            border_radius=16,
            alignment=ft.Alignment.CENTER,
        ),

        # Next / Prev Track Controls
        ft.Row([
            ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS_ROUNDED, icon_size=32, on_click=lambda _: play_track_index(current_idx[0] - 1)),
            ft.IconButton(icon=ft.Icons.SKIP_NEXT_ROUNDED, icon_size=32, on_click=lambda _: play_track_index(current_idx[0] + 1)),
        ], alignment=ft.MainAxisAlignment.CENTER),

        ft.Divider(),

        # Add Files & Playlist
        ft.Row([
            ft.Button("Add Media File 📁", icon=ft.Icons.FOLDER_OPEN_ROUNDED, on_click=pick_media_file, style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE)),
        ]),
        ft.Row([
            url_input,
            ft.IconButton(icon=ft.Icons.ADD_ROUNDED, bgcolor=ft.Colors.GREEN_700, icon_color=ft.Colors.WHITE, on_click=load_from_url),
        ]),

        ft.Text("Playlist Queue:", size=14, weight=ft.FontWeight.BOLD),
        playlist_column,
        ft.Divider(),
        ft.Text("Features:", size=13, color=ft.Colors.GREY_400),
        ft.Text("• Plays MP3, WAV, M4A, AAC, MP4 & Web Streams\n• Full hardware-accelerated playback\n• Playlist queue manager with skip controls", size=12, color=ft.Colors.GREY_500),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
