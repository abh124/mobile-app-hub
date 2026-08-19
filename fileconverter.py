import flet as ft
import os
import io
import base64
from PIL import Image

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def get_file_converter_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for File Converter (Images, Documents, PDFs)."""

    status_text = ft.Text("", size=13, weight=ft.FontWeight.W_500)

    # Helper for status messages
    def set_status(msg: str, color=ft.Colors.GREEN_400):
        status_text.value = msg
        status_text.color = color
        page.update()

    # --- TAB 1: IMAGE CONVERTER & RESIZER ---
    selected_img_bytes = [None]
    selected_img_name = [""]

    img_preview = ft.Image(
        src="",
        width=180,
        height=180,
        fit="contain",
        visible=False,
        border_radius=12,
    )


    img_info_text = ft.Text("No image selected", size=13, color=ft.Colors.GREY_400)

    target_format_dropdown = ft.Dropdown(
        label="Target Format",
        value="PNG",
        options=[
            ft.dropdown.Option("PNG"),
            ft.dropdown.Option("JPEG"),
            ft.dropdown.Option("WEBP"),
            ft.dropdown.Option("BMP"),
            ft.dropdown.Option("PDF"),
        ],
        border_radius=10,
        expand=True,
    )

    quality_slider = ft.Slider(min=10, max=100, value=85, label="{value}% Quality")
    resize_scale = ft.Dropdown(
        label="Resize Scale",
        value="100%",
        options=[
            ft.dropdown.Option("100%"),
            ft.dropdown.Option("75%"),
            ft.dropdown.Option("50%"),
            ft.dropdown.Option("25%"),
        ],
        border_radius=10,
        expand=True,
    )

    converted_img_preview = ft.Image(
        src="",
        width=180,
        height=180,
        fit="contain",
        visible=False,
        border_radius=12,
    )
    download_btn = ft.Container(visible=False)

    def on_img_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            picked_file = e.files[0]
            selected_img_name[0] = picked_file.name
            if picked_file.path and os.path.exists(picked_file.path):
                with open(picked_file.path, "rb") as f:
                    selected_img_bytes[0] = f.read()
            elif picked_file.bytes:
                selected_img_bytes[0] = picked_file.bytes

            if selected_img_bytes[0]:
                img = Image.open(io.BytesIO(selected_img_bytes[0]))
                img_info_text.value = f"Selected: {picked_file.name} ({img.width}x{img.height} px, {img.format})"
                img_preview.src_base64 = base64.b64encode(selected_img_bytes[0]).decode("utf-8")
                img_preview.visible = True
                set_status("Image loaded successfully!", ft.Colors.GREEN_400)
            else:
                set_status("Failed to read image data.", ft.Colors.RED_400)
        page.update()

    img_picker = ft.FilePicker()
    img_picker.on_result = on_img_picked
    if img_picker not in page.overlay:
        page.overlay.append(img_picker)

    def convert_image(_):
        if not selected_img_bytes[0]:
            set_status("Please select an image first!", ft.Colors.AMBER_400)
            return

        try:
            set_status("Converting image...", ft.Colors.BLUE_400)
            raw_img = Image.open(io.BytesIO(selected_img_bytes[0]))

            # Resize scale calculation
            scale = int(resize_scale.value.replace("%", "")) / 100.0
            new_w = max(1, int(raw_img.width * scale))
            new_h = max(1, int(raw_img.height * scale))
            res_img = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            fmt = target_format_dropdown.value.upper()
            output_io = io.BytesIO()

            if fmt == "JPEG" or fmt == "JPG":
                if res_img.mode in ("RGBA", "P"):
                    res_img = res_img.convert("RGB")
                res_img.save(output_io, format="JPEG", quality=int(quality_slider.value))
                ext = "jpg"
            elif fmt == "PDF":
                if res_img.mode in ("RGBA", "P"):
                    res_img = res_img.convert("RGB")
                res_img.save(output_io, format="PDF")
                ext = "pdf"
            elif fmt == "WEBP":
                res_img.save(output_io, format="WEBP", quality=int(quality_slider.value))
                ext = "webp"
            elif fmt == "BMP":
                if res_img.mode in ("RGBA", "P"):
                    res_img = res_img.convert("RGB")
                res_img.save(output_io, format="BMP")
                ext = "bmp"
            else: # PNG default
                res_img.save(output_io, format="PNG")
                ext = "png"

            out_bytes = output_io.getvalue()

            if fmt != "PDF":
                converted_img_preview.src_base64 = base64.b64encode(out_bytes).decode("utf-8")
                converted_img_preview.visible = True
            else:
                converted_img_preview.visible = False

            # Setup Download / Save
            def save_output_file(_):
                def on_save_result(e: ft.FilePickerResultEvent):
                    if e.path:
                        with open(e.path, "wb") as f:
                            f.write(out_bytes)
                        set_status(f"File saved to {os.path.basename(e.path)}!", ft.Colors.GREEN_400)

                save_picker = ft.FilePicker()
                save_picker.on_result = on_save_result
                page.overlay.append(save_picker)
                page.update()
                base_name = os.path.splitext(selected_img_name[0])[0] or "converted_file"
                save_picker.save_file(file_name=f"{base_name}_converted.{ext}")

            download_btn.content = ft.Button(
                f"Save Converted File (.{ext.upper()})",
                icon=ft.Icons.DOWNLOAD_ROUNDED,
                on_click=save_output_file,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            )
            download_btn.visible = True

            set_status(f"Success! Converted to {fmt} ({len(out_bytes) // 1024} KB)", ft.Colors.GREEN_400)
        except Exception as ex:
            set_status(f"Conversion error: {str(ex)}", ft.Colors.RED_400)
        page.update()

    image_tab_content = ft.Column([
        ft.Text("Image Converter & Resizer", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.Button(
                "Pick Image File",
                icon=ft.Icons.IMAGE_OUTLINED,
                on_click=lambda _: img_picker.pick_files(allow_multiple=False, file_type="image"),
            ),
        ]),
        img_info_text,
        img_preview,
        ft.Divider(),
        ft.Row([target_format_dropdown, resize_scale]),
        ft.Text("Quality / Compression:"),
        quality_slider,
        ft.Button("Convert Image", icon=ft.Icons.TRANSFORM, on_click=convert_image, style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE)),
        converted_img_preview,
        download_btn,
    ], spacing=12)

    # --- TAB 2: DOCUMENT & TEXT TO PDF CONVERTER ---
    doc_text_input = ft.TextField(
        hint_text="Paste or type text here to generate a Word (.docx) or PDF file...",
        multiline=True,
        min_lines=5,
        max_lines=10,
        border_radius=10,
    )
    doc_status = ft.Text("", size=13)

    def create_docx_file(_):
        txt = doc_text_input.value.strip()
        if not txt:
            doc_status.value = "Please enter some text first!"
            doc_status.color = ft.Colors.AMBER_400
            page.update()
            return

        def on_save_docx(e: ft.FilePickerResultEvent):
            if e.path:
                try:
                    if HAS_DOCX:
                        doc = docx.Document()
                        doc.add_heading("Generated Document", level=1)
                        for line in txt.split("\n"):
                            doc.add_paragraph(line)
                        doc.save(e.path)
                    else:
                        # Fallback plain text write with .docx extension
                        with open(e.path, "w", encoding="utf-8") as f:
                            f.write(txt)
                    doc_status.value = f"Saved to {os.path.basename(e.path)}!"
                    doc_status.color = ft.Colors.GREEN_400
                except Exception as ex:
                    doc_status.value = f"Error saving file: {ex}"
                    doc_status.color = ft.Colors.RED_400
                page.update()

        save_picker = ft.FilePicker()
        save_picker.on_result = on_save_docx
        page.overlay.append(save_picker)
        page.update()
        save_picker.save_file(file_name="Document.docx", allowed_extensions=["docx", "txt"])

    def create_pdf_from_text(_):
        txt = doc_text_input.value.strip()
        if not txt:
            doc_status.value = "Please enter some text first!"
            doc_status.color = ft.Colors.AMBER_400
            page.update()
            return

        def on_save_pdf(e: ft.FilePickerResultEvent):
            if e.path:
                try:
                    # Generate a clean PDF using PIL canvas rendering
                    lines = txt.split("\n")
                    # Create blank page image (A4 ratio approx)
                    img = Image.new("RGB", (1240, 1754), color="white")
                    from PIL import ImageDraw, ImageFont
                    draw = ImageDraw.Draw(img)
                    
                    y = 100
                    for line in lines:
                        draw.text((80, y), line, fill="black")
                        y += 40
                        if y > 1650:
                            break

                    pdf_bytes = io.BytesIO()
                    img.save(pdf_bytes, format="PDF")

                    with open(e.path, "wb") as f:
                        f.write(pdf_bytes.getvalue())

                    doc_status.value = f"PDF saved to {os.path.basename(e.path)}!"
                    doc_status.color = ft.Colors.GREEN_400
                except Exception as ex:
                    doc_status.value = f"PDF generation error: {ex}"
                    doc_status.color = ft.Colors.RED_400
                page.update()

        save_picker = ft.FilePicker()
        save_picker.on_result = on_save_pdf
        page.overlay.append(save_picker)
        page.update()
        save_picker.save_file(file_name="Converted_Document.pdf", allowed_extensions=["pdf"])

    doc_tab_content = ft.Column([
        ft.Text("Document & Text Converter", size=16, weight=ft.FontWeight.BOLD),
        doc_text_input,
        doc_status,
        ft.Row([
            ft.Button(
                "Export as Word (.DOCX)",
                icon=ft.Icons.DESCRIPTION_ROUNDED,
                on_click=create_docx_file,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            ),
            ft.Button(
                "Export as PDF (.PDF)",
                icon=ft.Icons.PICTURE_IN_PICTURE_ROUNDED,
                on_click=create_pdf_from_text,
                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
            ),
        ], wrap=True),
        ft.Divider(),
        ft.Text("Word (.docx) / File Features:", size=13, color=ft.Colors.GREY_400),
        ft.Text("• Convert images to PNG, JPG, WEBP, BMP & PDF\n• Scale and compress image file sizes\n• Export notes & text directly to Word (.docx) & PDF documents", size=12, color=ft.Colors.GREY_500),
    ], spacing=12)

    # --- MAIN TABS CONTAINER ---
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Image Converter", icon=ft.Icons.IMAGE_SEARCH_ROUNDED, content=image_tab_content),
            ft.Tab(text="Doc & Text to PDF", icon=ft.Icons.PICTURE_AS_PDF_ROUNDED, content=doc_tab_content),
        ],
        expand=True,
    )

    return ft.Column([
        status_text,
        tabs,
    ], expand=True, scroll=ft.ScrollMode.AUTO)
