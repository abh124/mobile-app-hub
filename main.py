import flet as ft
import time
import random
from bgremouve import get_bg_remover_control
from voicetools import get_voice_tool_control
from fileconverter import get_file_converter_control
from ytdownloader import get_yt_downloader_control


def main(page: ft.Page):
    page.title = "Multi-Hub Mobile App"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    
    # Configure phone window size preview for desktop
    page.window.width = 400
    page.window.height = 840
    page.window.resizable = True

    # App Data State
    tasks = []
    notes = []
    counter_val = 0

    # --- PAGE CONTENT SWAP HELPER ---
    body_container = ft.Column(scroll=ft.ScrollMode.AUTO)

    def show_home():
        body_container.controls.clear()
        body_container.controls.append(main_home_content)
        page.update()

    def open_tool_page(title: str, content_control: ft.Control):
        tool_view = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: show_home()),
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD, expand=True),
                ]),
                padding=ft.Padding(left=10, right=10, top=10, bottom=0),
            ),
            ft.Divider(height=10),
            ft.Container(
                content=content_control,
                padding=10,
                expand=True,
            ),
        ], scroll=ft.ScrollMode.AUTO)
        body_container.controls.clear()
        body_container.controls.append(tool_view)
        page.update()

    # --- 1. BACKGROUND REMOVER TOOL (IMPORTED FROM bgremouve.py) ---
    def open_bg_remover_tool(_):
        tool_content = get_bg_remover_control(page)
        open_tool_page("Background Remover 🖼️", tool_content)

    # --- 1b. VOICE TOOLS (IMPORTED FROM voicetools.py) ---
    def open_voice_tool(_):
        tool_content = get_voice_tool_control(page)
        open_tool_page("Voice Tools 🎙️", tool_content)

    # --- 1c. FILE CONVERTER (IMPORTED FROM fileconverter.py) ---
    def open_file_converter_tool(_):
        tool_content = get_file_converter_control(page)
        open_tool_page("File Converter 📄", tool_content)

    # --- 1d. YT DOWNLOADER (IMPORTED FROM ytdownloader.py) ---
    def open_yt_downloader_tool(_):
        tool_content = get_yt_downloader_control(page)
        open_tool_page("YouTube Downloader 🎬", tool_content)


    # --- 2. TASK MANAGER TOOL ---
    task_input = ft.TextField(hint_text="New task...", expand=True, border_radius=12)
    task_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=300)

    def refresh_tasks():
        task_col.controls.clear()
        if not tasks:
            task_col.controls.append(
                ft.Container(
                    content=ft.Text("No active tasks!", color=ft.Colors.GREY_500),
                    alignment=ft.Alignment.CENTER,
                    padding=20
                )
            )
        else:
            for idx, t in enumerate(tasks):
                def make_del(i):
                    return lambda _: (tasks.pop(i), refresh_tasks(), update_home_stats())
                def make_toggle(i):
                    return lambda e: (tasks[i].update({"done": e.control.value}), refresh_tasks())

                task_col.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=10,
                        border_radius=10,
                        content=ft.Row([
                            ft.Checkbox(value=t["done"], on_change=make_toggle(idx)),
                            ft.Text(
                                t["title"],
                                expand=True,
                                style=ft.TextStyle(
                                    decoration=ft.TextDecoration.LINE_THROUGH if t["done"] else ft.TextDecoration.NONE,
                                    color=ft.Colors.GREY_400 if t["done"] else ft.Colors.WHITE
                                )
                            ),
                            ft.IconButton(icon=ft.Icons.DELETE_OUTLINED, icon_color=ft.Colors.RED_400, on_click=make_del(idx))
                        ])
                    )
                )
        page.update()

    def add_new_task(_):
        if task_input.value.strip():
            tasks.append({"title": task_input.value.strip(), "done": False})
            task_input.value = ""
            refresh_tasks()
            update_home_stats()

    def open_tasks_tool(_):
        refresh_tasks()
        tool_content = ft.Column([
            ft.Row([
                task_input,
                ft.IconButton(icon=ft.Icons.ADD_ROUNDED, bgcolor=ft.Colors.INDIGO_600, icon_color=ft.Colors.WHITE, on_click=add_new_task)
            ]),
            task_col
        ], tight=True)
        open_tool_page("Task Manager 📝", tool_content)

    # --- 3. UNIT CONVERTER TOOL ---
    km_input = ft.TextField(label="Kilometers", value="1", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    conv_result = ft.Text("Result: 0.62 Miles", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)

    def run_conversion(_):
        try:
            val = float(km_input.value)
            conv_result.value = f"Result: {val * 0.621371:.2f} Miles"
        except ValueError:
            conv_result.value = "Enter a valid number"
        page.update()

    def open_converter_tool(_):
        tool_content = ft.Column([
            km_input,
            ft.Button("Convert to Miles", on_click=run_conversion, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
            conv_result,
        ], spacing=15, tight=True)
        open_tool_page("Unit Converter 🧮", tool_content)

    # --- 4. QUICK NOTES TOOL ---
    note_input = ft.TextField(hint_text="Type a quick note...", multiline=True, min_lines=2, border_radius=10)
    notes_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=250)

    def refresh_notes():
        notes_col.controls.clear()
        if not notes:
            notes_col.controls.append(ft.Text("No saved notes.", color=ft.Colors.GREY_500))
        else:
            for idx, n in enumerate(notes):
                def make_del_note(i):
                    return lambda _: (notes.pop(i), refresh_notes(), update_home_stats())

                notes_col.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=12,
                        border_radius=10,
                        content=ft.Row([
                            ft.Text(n, expand=True, size=14),
                            ft.IconButton(icon=ft.Icons.DELETE_OUTLINED, icon_color=ft.Colors.RED_400, on_click=make_del_note(idx))
                        ])
                    )
                )
        page.update()

    def save_note(_):
        if note_input.value.strip():
            notes.append(note_input.value.strip())
            note_input.value = ""
            refresh_notes()
            update_home_stats()

    def open_notes_tool(_):
        refresh_notes()
        tool_content = ft.Column([
            note_input,
            ft.Button("Save Note", icon=ft.Icons.SAVE_ROUNDED, on_click=save_note),
            ft.Divider(),
            notes_col
        ], tight=True)
        open_tool_page("Quick Notepad 📓", tool_content)

    # --- 5. RANDOM PICKER / DICE TOOL ---
    dice_result = ft.Text("🎲 Roll Result: -", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300)

    def roll_dice(_):
        res = random.randint(1, 6)
        dice_result.value = f"🎲 Roll Result: {res}"
        page.update()

    def open_dice_tool(_):
        tool_content = ft.Column([
            ft.Container(content=dice_result, alignment=ft.Alignment.CENTER, padding=20),
            ft.Button("Roll Dice", icon=ft.Icons.CASINO_ROUNDED, on_click=roll_dice),
        ], alignment=ft.MainAxisAlignment.CENTER, tight=True)
        open_tool_page("Random Dice Roll 🎲", tool_content)

    # --- 6. TIMER / COUNTER TOOL ---
    timer_text = ft.Text("Count: 0", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)

    def increment_counter():
        nonlocal counter_val
        counter_val += 1
        timer_text.value = f"Count: {counter_val}"
        update_home_stats()
        page.update()

    def reset_counter():
        nonlocal counter_val
        counter_val = 0
        timer_text.value = f"Count: {counter_val}"
        update_home_stats()
        page.update()

    def open_timer_tool(_):
        timer_text.value = f"Count: {counter_val}"
        tool_content = ft.Column([
            ft.Container(content=timer_text, alignment=ft.Alignment.CENTER, padding=15),
            ft.Row([
                ft.Button("Quick Counter +1", icon=ft.Icons.PLUS_ONE, on_click=lambda _: increment_counter()),
                ft.Button("Reset", icon=ft.Icons.REFRESH, on_click=lambda _: reset_counter()),
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], tight=True)
        open_tool_page("Quick Counter ⏱️", tool_content)

    # --- 7. FLASHLIGHT / SCREEN LIGHT TOOL ---
    def open_light_tool(_):
        light_box = ft.Container(
            bgcolor=ft.Colors.WHITE,
            height=200,
            border_radius=16,
            alignment=ft.Alignment.CENTER,
            content=ft.Text("Full Screen White Light", color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD)
        )
        open_tool_page("Screen Flashlight 💡", light_box)

    # --- 8. ANALYTICS / STATS TOOL ---
    def open_stats_tool(_):
        stats_content = ft.Column([
            ft.ListTile(leading=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400), title=ft.Text("Total Tasks"), trailing=ft.Text(f"{len(tasks)}")),
            ft.ListTile(leading=ft.Icon(ft.Icons.NOTE, color=ft.Colors.BLUE_400), title=ft.Text("Saved Notes"), trailing=ft.Text(f"{len(notes)}")),
            ft.ListTile(leading=ft.Icon(ft.Icons.PLUS_ONE, color=ft.Colors.AMBER_400), title=ft.Text("Counter Value"), trailing=ft.Text(f"{counter_val}")),
        ], tight=True)
        open_tool_page("App Analytics 📊", stats_content)

    # --- 9. SETTINGS TOOL ---
    def toggle_theme(e=None):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        theme_icon.icon = ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE
        page.update()

    def open_settings_tool(_):
        settings_content = ft.Column([
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                padding=12,
                border_radius=12,
                content=ft.Row([
                    ft.Text("Toggle Theme", size=16, expand=True),
                    ft.Switch(value=(page.theme_mode == ft.ThemeMode.LIGHT), on_change=lambda e: toggle_theme(e))
                ])
            ),
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                padding=12,
                border_radius=12,
                content=ft.Row([
                    ft.Text("App Mode", size=16, expand=True),
                    ft.Text("Single-Page Mobile Hub", color=ft.Colors.GREY_400)
                ])
            )
        ], tight=True)
        open_tool_page("Settings ⚙️", settings_content)

    # --- MAIN PAGE DASHBOARD CONTROLS ---
    task_stat_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)
    note_stat_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)
    counter_stat_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)

    def update_home_stats():
        task_stat_text.value = str(len(tasks))
        note_stat_text.value = str(len(notes))
        counter_stat_text.value = str(counter_val)
        page.update()

    theme_icon = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE,
        icon_color=ft.Colors.WHITE,
        on_click=toggle_theme,
    )

    # Grid Button Builder Helper
    def create_feature_button(title: str, subtitle: str, icon: str, color: str, on_click):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icon, color=ft.Colors.WHITE, size=28),
                    bgcolor=color,
                    padding=10,
                    border_radius=12,
                ),
                ft.Text(title, size=15, weight=ft.FontWeight.BOLD, max_lines=1),
                ft.Text(subtitle, size=12, color=ft.Colors.GREY_400, max_lines=1),
            ], spacing=6),
            padding=14,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=16,
            on_click=on_click,
            expand=True,
        )

    # SINGLE MAIN PAGE LAYOUT
    main_scrollable = ft.Column(
        controls=[
            # Hero Header Banner
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text("Mobile Tool Hub 🚀", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("Single Page Multi-Tool App", size=13, color=ft.Colors.GREY_300),
                        ]),
                        theme_icon,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ]),
                padding=20,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.TOP_LEFT,
                    end=ft.Alignment.BOTTOM_RIGHT,
                    colors=[ft.Colors.INDIGO_700, ft.Colors.PURPLE_800],
                ),
                border_radius=ft.BorderRadius.only(bottom_left=24, bottom_right=24),
            ),

            # Content Area
            ft.Container(
                padding=16,
                content=ft.Column([
                    # Quick Status Summary Row
                    ft.Text("Overview", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Tasks", size=12, color=ft.Colors.GREY_400),
                                task_stat_text,
                            ]),
                            padding=12,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=12,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Notes", size=12, color=ft.Colors.GREY_400),
                                note_stat_text,
                            ]),
                            padding=12,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=12,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Counter", size=12, color=ft.Colors.GREY_400),
                                counter_stat_text,
                            ]),
                            padding=12,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=12,
                            expand=True,
                        ),
                    ]),

                    ft.Divider(height=24, color=ft.Colors.TRANSPARENT),
                    ft.Text("Feature Buttons & Tools", size=18, weight=ft.FontWeight.BOLD),

                    # FEATURE BUTTONS: PRIMARY TOOLS
                    ft.Row([
                        create_feature_button("YT Downloader", "Video & MP3", ft.Icons.VIDEO_LIBRARY_ROUNDED, ft.Colors.RED_600, open_yt_downloader_tool),
                        create_feature_button("File Converter", "Docs & Images", ft.Icons.FILE_PRESENT_ROUNDED, ft.Colors.BLUE_ACCENT_700, open_file_converter_tool),
                    ]),

                    ft.Row([
                        create_feature_button("BG Remover", "Remove Photo BG", ft.Icons.AUTO_FIX_HIGH, ft.Colors.DEEP_ORANGE_600, open_bg_remover_tool),
                        create_feature_button("Voice Tools", "TTS & STT", ft.Icons.RECORD_VOICE_OVER, ft.Colors.PINK_600, open_voice_tool),
                    ]),



                    # GRID OF FEATURE BUTTONS (Row 1)
                    ft.Row([
                        create_feature_button("Task Manager", "To-Do & List", ft.Icons.CHECK_BOX_OUTLINED, ft.Colors.BLUE_600, open_tasks_tool),
                        create_feature_button("Converter", "KM to Miles", ft.Icons.CALCULATE, ft.Colors.AMBER_600, open_converter_tool),
                    ]),

                    # GRID OF FEATURE BUTTONS (Row 2)
                    ft.Row([
                        create_feature_button("Quick Notepad", "Save Notes", ft.Icons.NOTE_ALT_ROUNDED, ft.Colors.PURPLE_600, open_notes_tool),
                        create_feature_button("Dice Roller", "Random 1-6", ft.Icons.CASINO_ROUNDED, ft.Colors.TEAL_600, open_dice_tool),
                    ]),

                    # GRID OF FEATURE BUTTONS (Row 3)
                    ft.Row([
                        create_feature_button("Counter", "Quick Tally", ft.Icons.PLUS_ONE, ft.Colors.ORANGE_600, open_timer_tool),
                        create_feature_button("Screen Light", "Torch Light", ft.Icons.LIGHTBULB_ROUNDED, ft.Colors.YELLOW_700, open_light_tool),
                    ]),

                    # GRID OF FEATURE BUTTONS (Row 4)
                    ft.Row([
                        create_feature_button("Analytics", "App Summary", ft.Icons.BAR_CHART_ROUNDED, ft.Colors.GREEN_600, open_stats_tool),
                        create_feature_button("Settings", "App Config", ft.Icons.SETTINGS_ROUNDED, ft.Colors.GREY_700, open_settings_tool),
                    ]),
                ], spacing=12),
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    main_home_content = main_scrollable
    body_container.controls.append(main_home_content)
    page.add(body_container)
    update_home_stats()

if __name__ == "__main__":
    ft.run(main)
