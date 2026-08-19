import flet as ft
import os
import io
import base64

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    # pyrefly: ignore [missing-import]
    import rembg
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False


def remove_background_simple(image_bytes: bytes, tolerance: int = 30) -> bytes:
    """Removes light/white or solid background colors using PIL image processing."""
    if not HAS_PIL:
        return image_bytes

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    datas = img.getdata()

    # Determine background color from corners
    corner_pixels = [datas[0], datas[img.width - 1], datas[(img.height - 1) * img.width], datas[len(datas) - 1]]
    bg_r = sum(p[0] for p in corner_pixels) // len(corner_pixels)
    bg_g = sum(p[1] for p in corner_pixels) // len(corner_pixels)
    bg_b = sum(p[2] for p in corner_pixels) // len(corner_pixels)

    newData = []
    threshold = tolerance * 3.5

    for item in datas:
        r, g, b, a = item
        # Calculate Euclidean-like distance to background color
        diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
        
        # Also auto-remove pure white/near-white backgrounds if background is bright
        is_white_bg = (r > 230 and g > 230 and b > 230)
        
        if diff < threshold or is_white_bg:
            newData.append((255, 255, 255, 0))  # Transparent
        else:
            newData.append((r, g, b, a))

    img.putdata(newData)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def get_bg_remover_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for the Background Remover tool."""
    
    selected_file_path = [None]
    processed_bytes = [None]

    original_img = ft.Image(src="", width=150, height=150, fit=ft.BoxFit.CONTAIN, visible=False)
    result_img = ft.Image(src="", width=150, height=150, fit=ft.BoxFit.CONTAIN, visible=False)
    
    status_text = ft.Text("Paste image path or pick a file to remove background", color=ft.Colors.GREY_400, size=13)
    tolerance_slider = ft.Slider(min=5, max=80, value=30, label="{value}% Sensitivity")
    process_btn = ft.Button("Remove Background ✨", icon=ft.Icons.AUTO_FIX_HIGH, disabled=True)
    save_btn = ft.Button("Save PNG 💾", icon=ft.Icons.DOWNLOAD_ROUNDED, disabled=True)

    path_input = ft.TextField(
        hint_text="Paste full image file path here...",
        expand=True,
        border_radius=10,
    )

    def load_image_from_path(raw_path: str):
        clean_path = raw_path.strip('"\' ')
        if not clean_path:
            status_text.value = "Please enter or pick an image file path!"
            status_text.color = ft.Colors.RED_400
            page.update()
            return

        if not os.path.exists(clean_path):
            status_text.value = f"File not found: {os.path.basename(clean_path)}"
            status_text.color = ft.Colors.RED_400
            page.update()
            return

        try:
            selected_file_path[0] = clean_path
            with open(clean_path, "rb") as f:
                img_data = f.read()

            b64_str = base64.b64encode(img_data).decode("utf-8")
            original_img.src_base64 = b64_str
            original_img.visible = True
            
            result_img.visible = False
            save_btn.disabled = True
            process_btn.disabled = False
            status_text.value = f"Loaded: {os.path.basename(clean_path)}"
            status_text.color = ft.Colors.GREEN_400
        except Exception as ex:
            status_text.value = f"Error loading image: {str(ex)}"
            status_text.color = ft.Colors.RED_400

        page.update()

    def pick_image(_):
        import threading
        def _open_dialog():
            try:
                from tkinter import Tk, filedialog
                root = Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                file_path = filedialog.askopenfilename(
                    title="Select an Image",
                    filetypes=[
                        ("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                        ("All Files", "*.*"),
                    ]
                )
                root.destroy()
                if file_path:
                    path_input.value = file_path
                    load_image_from_path(file_path)
            except Exception as ex:
                status_text.value = f"File picker error: {str(ex)}"
                status_text.color = ft.Colors.RED_400
                page.update()
        # Run in thread so Flet UI doesn't freeze
        threading.Thread(target=_open_dialog, daemon=True).start()

    def do_remove_bg(_):
        if not selected_file_path[0]:
            status_text.value = "Please load an image first!"
            status_text.color = ft.Colors.RED_400
            page.update()
            return
            
        status_text.value = "Processing background removal..."
        status_text.color = ft.Colors.AMBER_400
        page.update()

        try:
            with open(selected_file_path[0], "rb") as f:
                raw_bytes = f.read()

            if HAS_REMBG:
                res_bytes = rembg.remove(raw_bytes)
            else:
                res_bytes = remove_background_simple(raw_bytes, tolerance=int(tolerance_slider.value))

            processed_bytes[0] = res_bytes
            b64_res = base64.b64encode(res_bytes).decode("utf-8")
            result_img.src_base64 = b64_res
            result_img.visible = True
            save_btn.disabled = False

            engine_used = "AI (rembg)" if HAS_REMBG else "Color Keying (PIL)"
            status_text.value = f"Background Removed ({engine_used})!"
            status_text.color = ft.Colors.GREEN_400
        except Exception as err:
            status_text.value = f"Error: {str(err)}"
            status_text.color = ft.Colors.RED_400

        page.update()

    process_btn.on_click = do_remove_bg

    def save_result(_):
        if processed_bytes[0] and selected_file_path[0]:
            base_dir = os.path.dirname(selected_file_path[0])
            base_name = os.path.splitext(os.path.basename(selected_file_path[0]))[0]
            out_name = f"no_bg_{base_name}.png"
            out_path = os.path.join(base_dir, out_name)
            
            with open(out_path, "wb") as f:
                f.write(processed_bytes[0])

            status_text.value = f"Saved: {out_name}"
            status_text.color = ft.Colors.CYAN_300
            page.update()

    save_btn.on_click = save_result

    def on_path_submit(_):
        if path_input.value and path_input.value.strip():
            load_image_from_path(path_input.value.strip())

    path_input.on_submit = on_path_submit

    return ft.Container(
        content=ft.Column([
            status_text,
            ft.Row([
                path_input,
                ft.IconButton(icon=ft.Icons.CHECK_ROUNDED, tooltip="Load Path", on_click=on_path_submit),
            ]),
            ft.Row([
                ft.Button("Choose File 📁", icon=ft.Icons.FOLDER_OPEN, on_click=pick_image),
                process_btn,
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text("Background Removal Sensitivity:", size=12, color=ft.Colors.GREY_400),
            tolerance_slider,
            ft.Row([
                ft.Column([
                    ft.Text("Original", size=12, weight=ft.FontWeight.BOLD),
                    original_img,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column([
                    ft.Text("Result (No BG)", size=12, weight=ft.FontWeight.BOLD),
                    result_img,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            save_btn,
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=10),
        padding=10,
    )
