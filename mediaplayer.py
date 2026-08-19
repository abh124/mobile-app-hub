import flet as ft
import os
import ctypes
import threading
import time
import webbrowser


def get_media_player_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for the In-App Audio Player."""

    status_text = ft.Text("No track playing.", size=12, color=ft.Colors.GREY_400)
    track_title = ft.Text("Audio Player 🎵", size=18, weight=ft.FontWeight.BOLD, max_lines=1)
    artist_name = ft.Text("Select an audio track to play", size=13, color=ft.Colors.INDIGO_300, max_lines=1)

    playlist = []
    current_idx = [-1]
    is_playing = [False]
    is_paused = [False]
    is_shuffle = [False]
    is_repeat = [False]
    duration_ms = [0]
    position_ms = [0]
    track_thread_active = [False]

    def set_status(msg: str, color=ft.Colors.GREEN_400):
        status_text.value = msg
        status_text.color = color
        page.update()

    def format_time(ms: int) -> str:
        secs = int(ms / 1000)
        mins = secs // 60
        secs = secs % 60
        return f"{mins:02d}:{secs:02d}"

    timeline_text = ft.Text("00:00 / 00:00", size=13, color=ft.Colors.GREY_400)
    timeline_slider = ft.Slider(min=0, max=100, value=0, disabled=True)

    play_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED,
        icon_size=64,
        icon_color=ft.Colors.INDIGO_400,
    )

    shuffle_btn = ft.IconButton(
        icon=ft.Icons.SHUFFLE_ROUNDED,
        icon_size=24,
        icon_color=ft.Colors.GREY_400,
    )

    repeat_btn = ft.IconButton(
        icon=ft.Icons.REPEAT_ROUNDED,
        icon_size=24,
        icon_color=ft.Colors.GREY_400,
    )

    # In-App Windows MCI Audio Engine
    def mci_send(cmd: str) -> str:
        if os.name == 'nt':
            buf = ctypes.create_unicode_buffer(128)
            ctypes.windll.winmm.mciSendStringW(cmd, buf, 128, None)
            return buf.value
        return ""

    def close_current_audio():
        if os.name == 'nt':
            mci_send("stop audio_alias")
            mci_send("close audio_alias")

    def play_audio_file(filepath: str, title: str):
        try:
            close_current_audio()
            track_title.value = title
            artist_name.value = f"Audio Track • {os.path.splitext(title)[1].upper().replace('.', '')}"

            if os.name == 'nt' and os.path.exists(filepath):
                # Native Windows In-App MCI Playback
                clean_fp = os.path.abspath(filepath)
                mci_send(f'open "{clean_fp}" type mpegvideo alias audio_alias')
                mci_send("play audio_alias")

                # Get duration
                dur_str = mci_send("status audio_alias length")
                try:
                    duration_ms[0] = int(dur_str)
                    timeline_slider.max = max(1, duration_ms[0])
                    timeline_slider.disabled = False
                except ValueError:
                    duration_ms[0] = 0
                    timeline_slider.disabled = True
            else:
                # Web / Mobile launch fallback
                if filepath.startswith("http://") or filepath.startswith("https://"):
                    page.launch_url(filepath)
                else:
                    webbrowser.open(filepath)

            is_playing[0] = True
            is_paused[0] = False
            play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
            play_btn.icon_color = ft.Colors.INDIGO_300
            set_status(f"Playing in app: {title}", ft.Colors.GREEN_400)

            # Start timeline progress monitoring loop
            track_thread_active[0] = True

            def _progress_loop():
                while track_thread_active[0] and is_playing[0]:
                    time.sleep(0.3)
                    if os.name == 'nt' and not is_paused[0]:
                        pos_str = mci_send("status audio_alias position")
                        mode_str = mci_send("status audio_alias mode")
                        try:
                            p = int(pos_str)
                            position_ms[0] = p
                            timeline_slider.value = min(timeline_slider.max, p)
                            timeline_text.value = f"{format_time(position_ms[0])} / {format_time(duration_ms[0])}"
                            page.update()
                        except ValueError:
                            pass

                        if mode_str == "stopped" and position_ms[0] >= duration_ms[0] - 500 and duration_ms[0] > 0:
                            is_playing[0] = False
                            play_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
                            play_btn.icon_color = ft.Colors.INDIGO_400
                            set_status("Track finished.", ft.Colors.GREY_400)
                            page.update()
                            # Auto next
                            if current_idx[0] + 1 < len(playlist):
                                play_track_index(current_idx[0] + 1)
                            break

            threading.Thread(target=_progress_loop, daemon=True).start()

        except Exception as ex:
            set_status(f"Playback error: {ex}", ft.Colors.RED_400)
        page.update()

    def toggle_play_pause(_):
        if not playlist or current_idx[0] < 0:
            if playlist:
                play_track_index(0)
            else:
                set_status("Please add an audio track first!", ft.Colors.AMBER_400)
            return

        if is_playing[0]:
            if os.name == 'nt':
                mci_send("pause audio_alias")
            is_playing[0] = False
            is_paused[0] = True
            play_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
            play_btn.icon_color = ft.Colors.INDIGO_400
            set_status("Playback Paused", ft.Colors.AMBER_400)
        else:
            if is_paused[0] and os.name == 'nt':
                mci_send("resume audio_alias")
                is_playing[0] = True
                is_paused[0] = False
                play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
                play_btn.icon_color = ft.Colors.INDIGO_300
                set_status("Resumed", ft.Colors.GREEN_400)
            else:
                play_track_index(current_idx[0])
        page.update()

    play_btn.on_click = toggle_play_pause

    def stop_playback(_):
        close_current_audio()
        is_playing[0] = False
        is_paused[0] = False
        position_ms[0] = 0
        timeline_slider.value = 0
        timeline_text.value = f"00:00 / {format_time(duration_ms[0])}"
        play_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
        play_btn.icon_color = ft.Colors.INDIGO_400
        set_status("Playback Stopped", ft.Colors.GREY_400)
        page.update()

    def on_seek_change(e):
        if os.name == 'nt' and duration_ms[0] > 0:
            target_ms = int(e.control.value)
            mci_send(f"seek audio_alias to {target_ms}")
            if is_playing[0]:
                mci_send("play audio_alias")

    timeline_slider.on_change = on_seek_change

    def toggle_shuffle(_):
        is_shuffle[0] = not is_shuffle[0]
        shuffle_btn.icon_color = ft.Colors.INDIGO_300 if is_shuffle[0] else ft.Colors.GREY_400
        set_status("Shuffle Enabled" if is_shuffle[0] else "Shuffle Disabled", ft.Colors.INDIGO_300)
        page.update()

    def toggle_repeat(_):
        is_repeat[0] = not is_repeat[0]
        repeat_btn.icon_color = ft.Colors.INDIGO_300 if is_repeat[0] else ft.Colors.GREY_400
        set_status("Repeat Enabled" if is_repeat[0] else "Repeat Disabled", ft.Colors.INDIGO_300)
        page.update()

    shuffle_btn.on_click = toggle_shuffle
    repeat_btn.on_click = toggle_repeat

    def play_track_index(idx: int):
        if not playlist:
            set_status("Playlist is empty! Add audio files below.", ft.Colors.AMBER_400)
            return

        if is_shuffle[0]:
            import random
            idx = random.randint(0, len(playlist) - 1)
        else:
            idx = idx % len(playlist)

        current_idx[0] = idx
        item = playlist[idx]
        play_audio_file(item["path"], item["title"])
        refresh_playlist_ui()

    # Playlist UI
    playlist_column = ft.Column(spacing=6)

    def refresh_playlist_ui():
        playlist_column.controls.clear()
        if not playlist:
            playlist_column.controls.append(
                ft.Container(
                    content=ft.Text("No tracks in playlist. Click 'Add Audio Track' below.", size=12, color=ft.Colors.GREY_500),
                    alignment=ft.Alignment.CENTER,
                    padding=20
                )
            )
        else:
            for idx, item in enumerate(playlist):
                def make_play(i):
                    return lambda _: play_track_index(i)

                is_curr = (idx == current_idx[0])
                playlist_column.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.INDIGO_950 if is_curr else ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=12,
                        border_radius=12,
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.HEADSET_ROUNDED if not is_curr else ft.Icons.GRAPHIC_EQ_ROUNDED,
                                color=ft.Colors.INDIGO_300 if is_curr else ft.Colors.GREY_400,
                                size=22
                            ),
                            ft.Column([
                                ft.Text(item["title"], expand=True, size=14, weight=ft.FontWeight.BOLD if is_curr else ft.FontWeight.NORMAL),
                                ft.Text(f"Audio Track • {os.path.splitext(item['title'])[1].upper()}", size=11, color=ft.Colors.GREY_400),
                            ], expand=True, spacing=2),
                            ft.IconButton(
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                icon_color=ft.Colors.INDIGO_300 if is_curr else ft.Colors.WHITE,
                                on_click=make_play(idx)
                            ),
                        ]),
                    )
                )
        page.update()

    def pick_audio_files(_):
        def _open():
            try:
                from tkinter import Tk, filedialog
                root = Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                fpaths = filedialog.askopenfilenames(
                    title="Select Audio Files",
                    filetypes=[
                        ("Audio Files", "*.mp3 *.wav *.m4a *.flac *.aac *.ogg"),
                        ("All Files", "*.*"),
                    ]
                )
                root.destroy()
                if fpaths:
                    for fp in fpaths:
                        if os.path.exists(fp):
                            t_title = os.path.basename(fp)
                            playlist.append({"title": t_title, "path": fp})
                    if current_idx[0] < 0 and playlist:
                        current_idx[0] = 0
                        play_audio_file(playlist[0]["path"], playlist[0]["title"])
                    refresh_playlist_ui()
            except Exception as ex:
                set_status(f"File picker error: {ex}", ft.Colors.RED_400)

        threading.Thread(target=_open, daemon=True).start()

    url_input = ft.TextField(hint_text="Or paste direct Audio URL...", border_radius=10, expand=True)

    def load_from_url(_):
        u = url_input.value.strip()
        if u:
            t_title = os.path.basename(u) or "Online Stream.mp3"
            playlist.append({"title": t_title, "path": u})
            current_idx[0] = len(playlist) - 1
            play_audio_file(u, t_title)
            refresh_playlist_ui()
            url_input.value = ""

    # Album Disc Banner
    album_disc = ft.Container(
        content=ft.Stack([
            ft.Container(
                width=160,
                height=160,
                border_radius=80,
                gradient=ft.LinearGradient(
                    colors=[ft.Colors.INDIGO_700, ft.Colors.PURPLE_900],
                ),
                border=ft.Border.all(3, ft.Colors.INDIGO_400),
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=64, color=ft.Colors.WHITE),
            ),
        ]),
        alignment=ft.Alignment.CENTER,
        padding=10,
    )

    return ft.Column([
        # Header
        ft.Row([
            ft.Text("Audio Player 🎵", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_300),
            ft.Icon(ft.Icons.GRAPHIC_EQ_ROUNDED, color=ft.Colors.INDIGO_400),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

        status_text,

        # Album Disc Banner
        ft.Container(
            content=ft.Column([
                album_disc,
                track_title,
                artist_name,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=16,
            border_radius=20,
            alignment=ft.Alignment.CENTER,
        ),

        # Live Timeline Slider
        ft.Column([
            timeline_slider,
            ft.Row([timeline_text], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0),

        # Playback Control Bar
        ft.Row([
            shuffle_btn,
            ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS_ROUNDED, icon_size=36, on_click=lambda _: play_track_index(current_idx[0] - 1)),
            play_btn,
            ft.IconButton(icon=ft.Icons.STOP_ROUNDED, icon_size=32, icon_color=ft.Colors.RED_400, on_click=stop_playback),
            ft.IconButton(icon=ft.Icons.SKIP_NEXT_ROUNDED, icon_size=36, on_click=lambda _: play_track_index(current_idx[0] + 1)),
            repeat_btn,
        ], alignment=ft.MainAxisAlignment.CENTER),

        ft.Divider(),

        # Add Audio Files
        ft.Row([
            ft.Button(
                "Add Audio Track 🎶",
                icon=ft.Icons.LIBRARY_MUSIC_ROUNDED,
                on_click=pick_audio_files,
                style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ]),
        ft.Row([
            url_input,
            ft.IconButton(icon=ft.Icons.ADD_ROUNDED, bgcolor=ft.Colors.INDIGO_800, icon_color=ft.Colors.WHITE, on_click=load_from_url),
        ]),

        ft.Text("Playlist Queue:", size=14, weight=ft.FontWeight.BOLD),
        playlist_column,
        ft.Divider(),
        ft.Text("Audio Player Features:", size=13, color=ft.Colors.GREY_400),
        ft.Text("• In-app audio playback for MP3, WAV, M4A, FLAC & AAC\n• Live timeline slider, position timer & seeking\n• In-app Shuffle, Repeat & Track Queue", size=12, color=ft.Colors.GREY_500),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
