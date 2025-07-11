from .extensions import NewelleExtension
from .handlers import TabButtonDescription, ErrorSeverity
from .ui.widgets import MultilineEntry
from gi.repository import Gtk, Gio
from threading import Thread 

class TTSSpeaker(NewelleExtension):
    id = "tts_speaker"
    name="TTS Speaker"

    def add_tab_menu_entries(self) -> list:
        return [
            TabButtonDescription("TTS Speaker", "audio-volume-high-symbolic", lambda x,y : self.open_tts_tab(x))
        ]

    def open_tts_tab(self, button):
        box = Gtk.Box(hexpand=True, vexpand=True, orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.FILL, valign=Gtk.Align.CENTER)
        entry = MultilineEntry()
        entry.set_margin_end(10)
        entry.set_margin_start(10)
        entry.set_margin_top(10)
        entry.set_margin_bottom(10)
        entry.set_hexpand(True)
        
        box.append(entry)
        button = Gtk.Button(css_classes=["suggested-action"], label="Speak")
        button.set_margin_end(10)
        button.set_margin_start(10)
        button.set_margin_top(10)
        button.set_margin_bottom(10)
        button.connect("clicked", self.speak, entry)
        box.append(button)
        tab = self.ui_controller.add_tab(box)
        tab.set_title("TTS Speaker")
        tab.set_icon(Gio.ThemedIcon(name="audio-volume-high-symbolic"))

    def speak(self, button, entry: MultilineEntry):
        text = entry.get_text()
        if self.tts is not None:
            # Start on another thread to not hang the UI
            Thread(target=self.tts.play_audio, args=(text,)).start()
        else:
            self.throw("TTS is not enabled", ErrorSeverity.ERROR)
