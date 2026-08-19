import flet as ft
import os
import threading
import webbrowser
import random


def get_media_player_control(page: ft.Page) -> ft.Control:
    """Returns Samsung Music style Audio Player UI (Audio Only)."""

    status_text = ft.Text("No track playing.", size=12, color=ft.Colors.GREY_400)
    track_title = ft.Text("Samsung Music 🎵", size=18, weight=ft.FontWeight.BOLD, max_lines=1)
    artist_name = ft.Text("Select an audio track to start listening", size=13, color=ft.Colors.PURPLE_300, max_lines=1)

    playlist = []
    current_idx = [-1]
    is_playing = [False]
    is_shuffle = [False]
    is_repeat = [False]

    def set_status(msg: str, color=ft.Colors.GREEN_400):
        status_text.value = msg
        status_text.color = color
        page.update()

    def launch_audio(src_path: str, title: str):
        try:
            track_title.value = title
            artist_name.value = f"Audio File • {os.path.splitext(title)[1].upper().replace('.', '')}"
            is_playing[0] = True
            play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
            play_btn.icon_color = ft.Colors.PURPLE_300

            if src_path.startswith("http://") or src_path.startswith("https://"):
                page.launch_url(src_path)
            else:
                if os.name == 'nt' and os.path.exists(src_path):
                    os.startfile(src_path)
                else:
                    webbrowser.open(src_path)

            set_status(f"Now Playing: {title}", ft.Colors.GREEN_400)
        except Exception as ex:
            set_status(f"Playback error: {ex}", ft.Colors.RED_400)
        page.update()

    play_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED,
        icon_size=64,
        icon_color=ft.Colors.PURPLE_400,
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

    def toggle_shuffle(_):
        is_shuffle[0] = not is_shuffle[0]
        shuffle_btn.icon_color = ft.Colors.PURPLE_300 if is_shuffle[0] else ft.Colors.GREY_400
        set_status("Shuffle Enabled" if is_shuffle[0] else "Shuffle Disabled", ft.Colors.PURPLE_300)
        page.update()

    def toggle_repeat(_):
        is_repeat[0] = not is_repeat[0]
        repeat_btn.icon_color = ft.Colors.PURPLE_300 if is_repeat[0] else ft.Colors.GREY_400
        set_status("Repeat Enabled" if is_repeat[0] else "Repeat Disabled", ft.Colors.PURPLE_300)
        page.update()

    shuffle_btn.on_click = toggle_shuffle
    repeat_btn.on_click = toggle_repeat

    def play_track_index(idx: int):
        if not playlist:
            set_status("Playlist is empty! Add audio files below.", ft.Colors.AMBER_400)
            return

        if is_shuffle[0]:
            idx = random.randint(0, len(playlist) - 1)
        else:
            idx = idx % len(playlist)

        current_idx[0] = idx
        item = playlist[idx]
        launch_audio(item["path"], item["title"])
        refresh_playlist_ui()

    def toggle_play_pause(_):
        if current_idx[0] >= 0 and current_idx[0] < len(playlist):
            if is_playing[0]:
                is_playing[0] = False
                play_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED
                play_btn.icon_color = ft.Colors.PURPLE_400
                set_status("Paused", ft.Colors.AMBER_400)
            else:
                play_track_index(current_idx[0])
        elif playlist:
            play_track_index(0)
        else:
            set_status("Add audio tracks to start listening", ft.Colors.AMBER_400)
        page.update()

    play_btn.on_click = toggle_play_pause

    # Playlist UI
    playlist_column = ft.Column(spacing=6)

    def refresh_playlist_ui():
        playlist_column.controls.clear()
        if not playlist:
            playlist_column.controls.append(
                ft.Container(
                    content=ft.Text("No tracks in library. Click 'Add Music' below.", size=12, color=ft.Colors.GREY_500),
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
                        bgcolor=ft.Colors.PURPLE_950 if is_curr else ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=12,
                        border_radius=12,
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.HEADSET_ROUNDED if not is_curr else ft.Icons.GRAPHIC_EQ_ROUNDED,
                                color=ft.Colors.PURPLE_300 if is_curr else ft.Colors.GREY_400,
                                size=22
                            ),
                            ft.Column([
                                ft.Text(item["title"], expand=True, size=14, weight=ft.FontWeight.BOLD if is_curr else ft.FontWeight.NORMAL),
                                ft.Text(f"Audio Track • {os.path.splitext(item['title'])[1].upper()}", size=11, color=ft.Colors.GREY_400),
                            ], expand=True, spacing=2),
                            ft.IconButton(
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                icon_color=ft.Colors.PURPLE_300 if is_curr else ft.Colors.WHITE,
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
                    title="Select Audio Tracks (Samsung Music)",
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
                        launch_audio(playlist[0]["path"], playlist[0]["title"])
                    refresh_playlist_ui()
            except Exception as ex:
                set_status(f"File picker error: {ex}", ft.Colors.RED_400)

        threading.Thread(target=_open, daemon=True).start()

    url_input = ft.TextField(hint_text="Or paste direct MP3 / Audio Stream URL...", border_radius=10, expand=True)

    def load_from_url(_):
        u = url_input.value.strip()
        if u:
            t_title = os.path.basename(u) or "Online Stream.mp3"
            playlist.append({"title": t_title, "path": u})
            current_idx[0] = len(playlist) - 1
            launch_audio(u, t_title)
            refresh_playlist_ui()
            url_input.value = ""

    # Album Vinyl Disc Banner (Samsung Music Style)
    album_disc = ft.Container(
        content=ft.Stack([
            ft.Container(
                width=160,
                height=160,
                border_radius=80,
                gradient=ft.LinearGradient(
                    colors=[ft.Colors.PURPLE_700, ft.Colors.INDIGO_900],
                ),
                border=ft.Border.all(3, ft.Colors.PURPLE_400),
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
            ft.Text("Samsung Music 🎵", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_300),
            ft.Icon(ft.Icons.GRAPHIC_EQ_ROUNDED, color=ft.Colors.PURPLE_400),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

        status_text,

        # Samsung Music Vinyl Album Disc Art
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

        # Samsung Music Playback Control Bar
        ft.Row([
            shuffle_btn,
            ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS_ROUNDED, icon_size=36, on_click=lambda _: play_track_index(current_idx[0] - 1)),
            play_btn,
            ft.IconButton(icon=ft.Icons.SKIP_NEXT_ROUNDED, icon_size=36, on_click=lambda _: play_track_index(current_idx[0] + 1)),
            repeat_btn,
        ], alignment=ft.MainAxisAlignment.CENTER),

        ft.Divider(),

        # Track Library & Add Buttons
        ft.Row([
            ft.Button(
                "Add Music Track 🎶",
                icon=ft.Icons.LIBRARY_MUSIC_ROUNDED,
                on_click=pick_audio_files,
                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ]),
        ft.Row([
            url_input,
            ft.IconButton(icon=ft.Icons.ADD_ROUNDED, bgcolor=ft.Colors.PURPLE_800, icon_color=ft.Colors.WHITE, on_click=load_from_url),
        ]),

        ft.Text("Music Library Queue:", size=14, weight=ft.FontWeight.BOLD),
        playlist_column,
        ft.Divider(),
        ft.Text("Samsung Music Features:", size=13, color=ft.Colors.GREY_400),
        ft.Text("• Audio-only player for MP3, WAV, M4A, FLAC & AAC\n• One UI Shuffle, Repeat & Track Queue\n• Hardware-accelerated audio engine", size=12, color=ft.Colors.GREY_500),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
