import flet as ft
import os
import threading


def get_media_player_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for the Media Player (Audio & Media Playback)."""

    status_text = ft.Text("No media loaded.", size=13, color=ft.Colors.GREY_400)
    track_title = ft.Text("Select an Audio or Video file", size=16, weight=ft.FontWeight.BOLD, max_lines=1)
    track_subtitle = ft.Text("Supports MP3, WAV, M4A, MP4, AAC & Web URLs", size=12, color=ft.Colors.GREY_400)

    duration_ms = [0]
    position_ms = [0]
    is_playing = [False]
    playlist = []
    current_idx = [-1]

    # Audio Control
    audio_player = ft.Audio(
        src="",
        autoplay=False,
        volume=1.0,
    )
    if audio_player not in page.overlay:
        page.overlay.append(audio_player)

    timeline_text = ft.Text("00:00 / 00:00", size=13, color=ft.Colors.GREY_400)
    timeline_slider = ft.Slider(min=0, max=100, value=0, disabled=True)

    play_pause_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED,
        icon_color=ft.Colors.GREEN_400,
        icon_size=54,
    )

    volume_slider = ft.Slider(min=0, max=100, value=100, label="{value}% Vol", width=120)

    def format_time(ms: int) -> str:
        secs = int(ms / 1000)
        mins = secs // 60
        secs = secs % 60
        return f"{mins:02d}:{secs:02d}"

    def on_duration(e):
        if e.duration:
            duration_ms[0] = int(e.duration)
            timeline_slider.max = max(1, duration_ms[0])
            timeline_slider.disabled = False
            timeline_text.value = f"{format_time(position_ms[0])} / {format_time(duration_ms[0])}"
            page.update()

    def on_position(e):
        if e.position:
            position_ms[0] = int(e.position)
            if not timeline_slider.disabled:
                timeline_slider.value = min(timeline_slider.max, position_ms[0])
            timeline_text.value = f"{format_time(position_ms[0])} / {format_time(duration_ms[0])}"
            page.update()

    def on_state(e):
        if e.data == "completed":
            is_playing[0] = False
            play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
            play_pause_btn.icon_color = ft.Colors.GREEN_400
            # Auto-play next track if available
            if current_idx[0] + 1 < len(playlist):
                play_track_index(current_idx[0] + 1)
            page.update()

    audio_player.on_duration_change = on_duration
    audio_player.on_position_change = on_position
    audio_player.on_state_change = on_state

    def load_media_src(src_path: str, title: str):
        try:
            audio_player.src = src_path
            track_title.value = title
            track_subtitle.value = f"Source: {os.path.basename(src_path)}"
            status_text.value = f"Loaded: {title}"
            status_text.color = ft.Colors.GREEN_400

            # Start playback
            audio_player.play()
            is_playing[0] = True
            play_pause_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
            play_pause_btn.icon_color = ft.Colors.AMBER_400
        except Exception as ex:
            status_text.value = f"Media load error: {ex}"
            status_text.color = ft.Colors.RED_400
        page.update()

    def toggle_play_pause(_):
        if not audio_player.src:
            status_text.value = "Please select or add a media file first!"
            status_text.color = ft.Colors.AMBER_400
            page.update()
            return

        if is_playing[0]:
            audio_player.pause()
            is_playing[0] = False
            play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
            play_pause_btn.icon_color = ft.Colors.GREEN_400
        else:
            audio_player.resume()
            is_playing[0] = True
            play_pause_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
            play_pause_btn.icon_color = ft.Colors.AMBER_400
        page.update()

    play_pause_btn.on_click = toggle_play_pause

    def stop_playback(_):
        if audio_player.src:
            audio_player.pause()
            audio_player.seek(0)
            is_playing[0] = False
            play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
            play_pause_btn.icon_color = ft.Colors.GREEN_400
            position_ms[0] = 0
            timeline_slider.value = 0
            timeline_text.value = f"00:00 / {format_time(duration_ms[0])}"
            status_text.value = "Playback stopped."
            page.update()

    def on_seek_change(e):
        if audio_player.src and duration_ms[0] > 0:
            target_ms = int(e.control.value)
            audio_player.seek(target_ms)

    timeline_slider.on_change = on_seek_change

    def on_volume_change(e):
        vol = float(e.control.value) / 100.0
        audio_player.volume = vol
        page.update()

    volume_slider.on_change = on_volume_change

    # Pick media file (using non-blocking thread dialog)
    playlist_column = ft.Column(spacing=6)

    def refresh_playlist_ui():
        playlist_column.controls.clear()
        if not playlist:
            playlist_column.controls.append(ft.Text("Playlist is empty. Click 'Add File' above.", size=12, color=ft.Colors.GREY_500))
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
                            ft.IconButton(icon=ft.Icons.PLAY_ARROW_ROUNDED, icon_size=18, on_click=make_play(idx)),
                        ]),
                    )
                )
        page.update()

    def play_track_index(idx: int):
        if 0 <= idx < len(playlist):
            current_idx[0] = idx
            item = playlist[idx]
            load_media_src(item["path"], item["title"])
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
                    load_media_src(fpath, t_title)
                    refresh_playlist_ui()
            except Exception as ex:
                status_text.value = f"File picker error: {ex}"
                status_text.color = ft.Colors.RED_400
                page.update()

        threading.Thread(target=_open, daemon=True).start()

    url_input = ft.TextField(hint_text="Or paste direct Audio/Video URL...", border_radius=10, expand=True)

    def load_from_url(_):
        u = url_input.value.strip()
        if u:
            t_title = os.path.basename(u) or "Web Stream"
            playlist.append({"title": t_title, "path": u})
            current_idx[0] = len(playlist) - 1
            load_media_src(u, t_title)
            refresh_playlist_ui()
            url_input.value = ""

    return ft.Column([
        ft.Text("Media Player 🎵", size=18, weight=ft.FontWeight.BOLD),
        status_text,

        # Album Art & Banner Visualizer
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.MUSIC_VIDEO_ROUNDED, size=64, color=ft.Colors.INDIGO_400),
                track_title,
                track_subtitle,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=20,
            border_radius=16,
            alignment=ft.Alignment.CENTER,
        ),

        # Timeline Slider & Timer
        ft.Column([
            timeline_slider,
            ft.Row([timeline_text], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0),

        # Playback Controls
        ft.Row([
            ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS_ROUNDED, icon_size=32, on_click=lambda _: play_track_index(current_idx[0] - 1)),
            play_pause_btn,
            ft.IconButton(icon=ft.Icons.STOP_ROUNDED, icon_size=32, icon_color=ft.Colors.RED_400, on_click=stop_playback),
            ft.IconButton(icon=ft.Icons.SKIP_NEXT_ROUNDED, icon_size=32, on_click=lambda _: play_track_index(current_idx[0] + 1)),
        ], alignment=ft.MainAxisAlignment.CENTER),

        # Volume Controls
        ft.Row([
            ft.Icon(ft.Icons.VOLUME_DOWN_ROUNDED, size=20, color=ft.Colors.GREY_400),
            volume_slider,
            ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=20, color=ft.Colors.GREY_400),
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
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
