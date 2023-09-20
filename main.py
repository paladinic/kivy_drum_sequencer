import kivy
from kivy.app import App
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.core.audio import SoundLoader
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from concurrent.futures import ThreadPoolExecutor
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color

kivy.require('2.2.1')

instrument_sounds = {
    'H': "instruments/hat.wav",
    'S': "instruments/snare.wav",
    'K': "instruments/kick.wav",
}


class BeatCell(Widget):
    def __init__(self, **kwargs):
        super(BeatCell, self).__init__(**kwargs)
        
        with self.canvas:
            self.color = Color(1, 1, 1)  # Initial color (white)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def highlight(self):
        self.color.rgb = (0.5, 0.5, 0.5)  # Highlighted color (grey)

    def reset(self):
        self.color.rgb = (1, 1, 1)  # Reset to white


class MyApp(App):
    def __init__(self, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.executor = ThreadPoolExecutor(max_workers=3)  # 3 instruments
        # Preload all sounds
        self.sounds = {}
        for label, path in instrument_sounds.items():
            sound = SoundLoader.load(path)
            if not sound:
                print(f"Failed to load sound from {path}")
            else:
                self.sounds[label] = sound

    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.create_buttons()
        self.create_beat_row()
        self.create_slider()
        return self.layout

    def create_buttons(self):
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=100)
        start_button = Button(text='Start', on_release=self.start_sound)
        stop_button = Button(text='Stop', on_release=self.stop_sound)
        button_layout.add_widget(start_button)
        button_layout.add_widget(stop_button)
        self.layout.add_widget(button_layout)
        self.instrument_labels = ['K', 'S', 'H']
        self.instrument_buttons = []
        self.grid_layout = GridLayout(cols=16, spacing=5)
        
        color_map = {
            'K': [0, 1, 0, 1],  # green in rgba
            'S': [0, 1, 1, 1],  # cyan in rgba
            'H': [0, 0, 1, 1]   # blue in rgba
        }

        for instrument_label in self.instrument_labels:
            instrument_buttons_row = []
            for _ in range(16):
                button = ToggleButton(background_color=color_map[instrument_label], group=None)
                instrument_buttons_row.append(button)
                self.grid_layout.add_widget(button)
            self.instrument_buttons.append(instrument_buttons_row)
        self.layout.add_widget(self.grid_layout)


    def create_beat_row(self):
        self.beat_row = GridLayout(cols=16, spacing=5, size_hint_y=0.15)
        for _ in range(16):
            cell = BeatCell()
            self.beat_row.add_widget(cell)
        self.layout.add_widget(self.beat_row)

    def update_bpm_label(self, instance, value):
        self.bpm_label.text = f"{int(value)} BPM"

    def create_slider(self):
        slider_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        self.slider = Slider(min=40, max=200, value=120)
        self.slider.bind(value=self.update_bpm_label)
        self.bpm_label = Label(text=f"{int(self.slider.value)} BPM", size_hint_x=None, width=100)
        slider_layout.add_widget(self.slider)
        slider_layout.add_widget(self.bpm_label)
        self.layout.add_widget(slider_layout)

    def start_sound(self, instance):
        self.playing = True
        self.current_beat = 0
        self.schedule_beat_highlight()

    def stop_sound(self, instance):
        self.playing = False
        # Reset all beat highlights
        for cell in self.beat_row.children:
            cell.reset()

    def play_sound(self, sound):
        sound.play()

    def schedule_beat_highlight(self, dt=0):
        # If the playing flag is set to False, exit the function
        if not self.playing:
            return

        # Reset the previous beat's highlight
        if self.current_beat != 0:
            prev_beat = self.current_beat - 1
        else:
            prev_beat = 15
        self.beat_row.children[-(prev_beat + 1)].reset()

        # Highlight current beat
        self.beat_row.children[-(self.current_beat + 1)].highlight()

        # Play sounds for the current beat
        for idx, instrument_label in enumerate(self.instrument_labels):
            if self.instrument_buttons[idx][self.current_beat].state == 'down':
                self.play_sound(self.sounds[instrument_label])

        # Schedule the next beat highlight
        self.current_beat = (self.current_beat + 1) % 16
        interval = 30.0 / self.slider.value
        Clock.schedule_once(self.schedule_beat_highlight, interval)


if __name__ == '__main__':
    MyApp().run()