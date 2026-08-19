import flet as ft
import math


def get_compass_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for the Interactive Mobile Compass Tool."""

    current_deg = [0]

    # Helper function to get direction name from angle
    def get_direction_name(deg: float) -> str:
        deg = deg % 360
        dirs = [
            ("N - North", 0, 22.5),
            ("NE - North East", 22.5, 67.5),
            ("E - East", 67.5, 112.5),
            ("SE - South East", 112.5, 157.5),
            ("S - South", 157.5, 202.5),
            ("SW - South West", 202.5, 247.5),
            ("W - West", 247.5, 292.5),
            ("NW - North West", 292.5, 337.5),
            ("N - North", 337.5, 360),
        ]
        for name, start, end in dirs:
            if start <= deg < end:
                return name
        return "N - North"

    heading_text = ft.Text("0° N", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400)
    direction_label = ft.Text("North", size=16, color=ft.Colors.GREY_300, weight=ft.FontWeight.W_500)

    # Stylized Needle Pointer
    needle_shape = ft.Column([
        ft.Icon(ft.Icons.NAVIGATION_ROUNDED, color=ft.Colors.RED_500, size=54),  # Red North Arrow
        ft.Container(height=4),
        ft.Icon(ft.Icons.NAVIGATION_ROUNDED, color=ft.Colors.BLUE_400, size=38, rotate=ft.Rotate(math.pi)),  # Blue South Arrow
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    needle_container = ft.Container(
        content=needle_shape,
        alignment=ft.Alignment.CENTER,
        rotate=ft.Rotate(angle=0, animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT)),
    )

    # Compass Rose Dial
    compass_dial = ft.Container(
        width=240,
        height=240,
        border_radius=120,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        border=ft.Border.all(3, ft.Colors.INDIGO_600),
        content=ft.Stack([
            # Cardinal Markings
            ft.Container(content=ft.Text("N", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400), alignment=ft.Alignment.TOP_CENTER, padding=8),
            ft.Container(content=ft.Text("S", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400), alignment=ft.Alignment.BOTTOM_CENTER, padding=8),
            ft.Container(content=ft.Text("E", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400), alignment=ft.Alignment.CENTER_RIGHT, padding=8),
            ft.Container(content=ft.Text("W", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400), alignment=ft.Alignment.CENTER_LEFT, padding=8),
            # Central Needle
            needle_container,
        ]),
        alignment=ft.Alignment.CENTER,
    )

    def update_compass_heading(deg_val: float):
        current_deg[0] = deg_val % 360
        angle_rad = math.radians(-current_deg[0])
        needle_container.rotate.angle = angle_rad
        heading_text.value = f"{int(current_deg[0])}°"
        direction_label.value = get_direction_name(current_deg[0])
        slider.value = current_deg[0]
        page.update()

    def on_slider_change(e):
        update_compass_heading(float(e.control.value))

    slider = ft.Slider(
        min=0,
        max=360,
        value=0,
        divisions=360,
        label="{value}°",
        on_change=on_slider_change,
    )

    # Preset direction buttons
    def set_preset(deg: float):
        update_compass_heading(deg)

    preset_row = ft.Row([
        ft.Button("N (0°)", on_click=lambda _: set_preset(0), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
        ft.Button("E (90°)", on_click=lambda _: set_preset(90), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
        ft.Button("S (180°)", on_click=lambda _: set_preset(180), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
        ft.Button("W (270°)", on_click=lambda _: set_preset(270), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
    ], alignment=ft.MainAxisAlignment.CENTER, wrap=True)

    qibla_button = ft.Button(
        "Qibla Finder (135° SE) 🕋",
        icon=ft.Icons.EXPLORE_ROUNDED,
        on_click=lambda _: set_preset(135),
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)),
    )

    return ft.Column([
        ft.Text("Digital Compass 🧭", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("Real-time directional heading & orientation finder", size=12, color=ft.Colors.GREY_400),
        ft.Container(
            content=ft.Column([
                heading_text,
                direction_label,
                ft.Container(height=10),
                compass_dial,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=10,
        ),
        ft.Text("Rotate Compass Heading:"),
        slider,
        preset_row,
        ft.Container(content=qibla_button, alignment=ft.Alignment.CENTER, padding=10),
        ft.Divider(),
        ft.Text("Features:", size=13, color=ft.Colors.GREY_400),
        ft.Text("• 360° Smooth Magnetic Rotation Needle\n• Quick Cardinal Presets (North, East, South, West)\n• Integrated Qibla Direction Finder (135° SE)", size=12, color=ft.Colors.GREY_500),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
