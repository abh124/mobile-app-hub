# pyrefly: ignore [missing-import]
import flet as ft
import threading

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

try:
    import speech_recognition as sr
    HAS_STT = True
except ImportError:
    HAS_STT = False


def get_voice_tool_control(page: ft.Page) -> ft.Control:
    """Returns the Flet Control UI for Text-to-Speech and Speech-to-Text."""

    # --- TEXT TO SPEECH (TTS) ---
    tts_input = ft.TextField(
        hint_text="Type text here to convert to speech...",
        multiline=True,
        min_lines=3,
        max_lines=6,
        border_radius=10,
        expand=True,
    )
    tts_status = ft.Text("", size=12, color=ft.Colors.GREY_400)
    tts_speaking = [False]

    # Speed slider
    tts_speed = ft.Slider(min=80, max=250, value=150, label="{value} WPM")

    def speak_text(_):
        if not HAS_TTS:
            tts_status.value = "pyttsx3 not installed! Run: pip install pyttsx3"
            tts_status.color = ft.Colors.RED_400
            page.update()
            return

        text = tts_input.value
        if not text or not text.strip():
            tts_status.value = "Please enter some text first!"
            tts_status.color = ft.Colors.AMBER_400
            page.update()
            return

        if tts_speaking[0]:
            tts_status.value = "Already speaking... please wait."
            tts_status.color = ft.Colors.AMBER_400
            page.update()
            return

        tts_speaking[0] = True
        tts_status.value = "🔊 Speaking..."
        tts_status.color = ft.Colors.GREEN_400
        page.update()

        def _speak():
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', int(tts_speed.value))
                engine.say(text.strip())
                engine.runAndWait()
                engine.stop()
                tts_status.value = "✅ Done speaking!"
                tts_status.color = ft.Colors.GREEN_400
            except Exception as ex:
                tts_status.value = f"TTS Error: {str(ex)}"
                tts_status.color = ft.Colors.RED_400
            finally:
                tts_speaking[0] = False
                page.update()

        threading.Thread(target=_speak, daemon=True).start()

    def stop_speaking(_):
        try:
            engine = pyttsx3.init()
            engine.stop()
        except:
            pass
        tts_speaking[0] = False
        tts_status.value = "Stopped."
        tts_status.color = ft.Colors.GREY_400
        page.update()

    # --- SPEECH TO TEXT (STT) ---
    stt_output = ft.TextField(
        hint_text="Recognized text will appear here...",
        multiline=True,
        min_lines=3,
        max_lines=6,
        border_radius=10,
        read_only=True,
        expand=True,
    )
    stt_status = ft.Text("", size=12, color=ft.Colors.GREY_400)
    stt_listening = [False]

    def listen_microphone(_):
        if not HAS_STT:
            stt_status.value = "SpeechRecognition not installed! Run: pip install SpeechRecognition"
            stt_status.color = ft.Colors.RED_400
            page.update()
            return

        if stt_listening[0]:
            stt_status.value = "Already listening..."
            stt_status.color = ft.Colors.AMBER_400
            page.update()
            return

        stt_listening[0] = True
        stt_status.value = "🎙️ Listening... Speak now!"
        stt_status.color = ft.Colors.CYAN_300
        page.update()

        def _listen():
            try:
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)

                stt_status.value = "🔄 Processing speech..."
                stt_status.color = ft.Colors.AMBER_400
                page.update()

                text = recognizer.recognize_google(audio)
                stt_output.value = text
                stt_output.read_only = False
                stt_status.value = "✅ Speech recognized!"
                stt_status.color = ft.Colors.GREEN_400
            except sr.WaitTimeoutError:
                stt_status.value = "⏰ Timeout - no speech detected. Try again."
                stt_status.color = ft.Colors.AMBER_400
            except sr.UnknownValueError:
                stt_status.value = "❌ Could not understand the audio. Try again."
                stt_status.color = ft.Colors.RED_400
            except sr.RequestError as e:
                stt_status.value = f"❌ API Error: {str(e)}"
                stt_status.color = ft.Colors.RED_400
            except Exception as ex:
                stt_status.value = f"❌ Error: {str(ex)}"
                stt_status.color = ft.Colors.RED_400
            finally:
                stt_listening[0] = False
                page.update()

        threading.Thread(target=_listen, daemon=True).start()

    def copy_stt_text(_):
        if stt_output.value and stt_output.value.strip():
            page.set_clipboard(stt_output.value.strip())
            stt_status.value = "📋 Copied to clipboard!"
            stt_status.color = ft.Colors.CYAN_300
            page.update()

    def send_stt_to_tts(_):
        if stt_output.value and stt_output.value.strip():
            tts_input.value = stt_output.value.strip()
            page.update()

    # --- BUILD LAYOUT ---
    return ft.Container(
        content=ft.Column([
            # TTS Section
            ft.Text("Text to Speech 🔊", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Type text below and press Speak to hear it.", size=12, color=ft.Colors.GREY_400),
            tts_input,
            ft.Text("Speech Speed:", size=12, color=ft.Colors.GREY_400),
            tts_speed,
            ft.Row([
                ft.Button("Speak ▶️", icon=ft.Icons.VOLUME_UP, on_click=speak_text),
                ft.Button("Stop ⏹", icon=ft.Icons.STOP, on_click=stop_speaking),
            ]),
            tts_status,

            ft.Divider(height=24),

            # STT Section
            ft.Text("Speech to Text 🎙️", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Press Record and speak into your microphone.", size=12, color=ft.Colors.GREY_400),
            ft.Row([
                ft.Button("Record 🎙️", icon=ft.Icons.MIC, on_click=listen_microphone),
                ft.Button("Copy 📋", icon=ft.Icons.COPY, on_click=copy_stt_text),
                ft.Button("→ TTS", icon=ft.Icons.ARROW_FORWARD, on_click=send_stt_to_tts, tooltip="Send to Text-to-Speech"),
            ]),
            stt_status,
            stt_output,
        ], spacing=10, scroll=ft.ScrollMode.AUTO),
        padding=10,
    )
