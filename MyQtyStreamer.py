import sys
import os
import os, sys
os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QLabel, QListWidget, QFileDialog, QSlider, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import mpv


class MPVStreamerPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MPV Streamer Music Player")
        self.setGeometry(200, 200, 700, 420)

        # MPV player instance
        self.player = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True)

        # Playlist
        self.playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat = False
        self.is_playing = False

        self.build_ui()
        self.setup_mpv_events()
        self.setup_timers()
        self.setStyleSheet("""
        QWidget {
            background-color: #2c2c2c;
            color: white;
            font-size: 14px;
        }
        #mainFrame {
            background-color: #292929;
            border-radius: 12px;
            padding: 10px;
        }
        QPushButton {
            background-color: #202020;
            border: 2px solid #555;
            padding: 8px 14px;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #4b4b4b;
        }
        QPushButton:pressed {
            background-color: #666;
        }
        QLabel {
            color: #dcdcdc;
        }
    """)

    def build_ui(self):
        main = QVBoxLayout()

        # Top layout: Now playing + stream URL
        top = QHBoxLayout()

        self.now_label = QLabel("No track playing")
        top.addWidget(self.now_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste stream URL and click Play Stream")
        

        self.play_stream_btn = QPushButton("Play Stream")
        self.play_stream_btn.clicked.connect(self.play_stream)
        top.addWidget(self.play_stream_btn)

        main.addLayout(top)

        # Center layout: Playlist + Controls
        center = QHBoxLayout()

        # Playlist
        self.list_widget = QListWidget()
        self.list_widget.doubleClicked.connect(self.play_selected_item)
        center.addWidget(self.list_widget, 2)


        right = QVBoxLayout()

        # Playback buttons
        ctrl = QHBoxLayout()
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.clicked.connect(self.prev_track)
        ctrl.addWidget(self.prev_btn)

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_pause)
        ctrl.addWidget(self.play_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop)
        ctrl.addWidget(self.stop_btn)

        self.next_btn = QPushButton("⏭")
        self.next_btn.clicked.connect(self.next_track)
        ctrl.addWidget(self.next_btn)
        right.addLayout(ctrl)

        # Progress slider
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderReleased.connect(self.seek_position)
        right.addWidget(self.progress)

        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        right.addWidget(self.time_label)

        # Volume slider
        vol = QHBoxLayout()
        vol.addWidget(QLabel("Vol"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.set_volume)
        vol.addWidget(self.volume_slider)
        right.addLayout(vol)

        # Playlist buttons
        pl = QHBoxLayout()
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        pl.addWidget(self.add_files_btn)

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_selected)
        pl.addWidget(self.remove_btn)

        self.shuffle_btn = QPushButton("Shuffle: Off")
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        pl.addWidget(self.shuffle_btn)

        self.repeat_btn = QPushButton("Repeat: Off")
        self.repeat_btn.clicked.connect(self.toggle_repeat)
        pl.addWidget(self.repeat_btn)

        right.addLayout(pl)

        center.addLayout(right, 3)
        main.addLayout(center)

        self.setLayout(main)

    # -------------------- MPV EVENTS --------------------
    def setup_mpv_events(self):
        @self.player.property_observer("time-pos")
        def time_observer(_name, value):
            if value and self.player.duration:
                pos = int(value / self.player.duration * 1000)
                self.progress.setValue(pos)

        @self.player.property_observer("duration")
        def duration_observer(_name, value):
            self.update_time_label()

        @self.player.property_observer("paused")
        def paused_observer(_name, val):
            if val:
                self.play_btn.setText("Play")
            else:
                self.play_btn.setText("Pause")

        @self.player.event_callback("end-file")
        def end_file(event):
            if self.repeat:
                self.play_current()
            else:
                self.next_track()

    # TIMERS ---
    def setup_timers(self):
        timer = QTimer(self)
        timer.setInterval(500)
        timer.timeout.connect(self.update_time_label)
        timer.start()

    # PLAYBACK ACTIONS ---
    def play_current(self):
        if 0 <= self.current_index < len(self.playlist):
            path = self.playlist[self.current_index]["path"]
            self.player.play(path)
            self.now_label.setText(f"Playing: {os.path.basename(path)}")
            self.play_btn.setText("Pause")
        else:
            QMessageBox.information(self, "Playlist Empty", "Add audio files first.")

    def play_pause(self):
        if self.player.pause:
            self.player.pause = False
        else:
            if self.current_index == -1 and self.playlist:
                self.current_index = 0
                self.play_current()
            else:
                self.player.pause = True

    def stop(self):
        self.player.stop()
        self.now_label.setText("Stopped")
        self.play_btn.setText("Play")

    def next_track(self):
        if not self.playlist:
            return

        if self.shuffle:
            self.current_index = random.randrange(len(self.playlist))
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)

        self.list_widget.setCurrentRow(self.current_index)
        self.play_current()

    def prev_track(self):
        if not self.playlist:
            return

        if self.shuffle:
            self.current_index = random.randrange(len(self.playlist))
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)

        self.list_widget.setCurrentRow(self.current_index)
        self.play_current()

    def play_selected_item(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.current_index = row
            self.play_current()

    # STREAM URL ---
    def play_stream(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "No URL", "Paste a stream URL first.")
            return

        self.player.play(url)
        self.now_label.setText(f"Streaming: {url}")
        self.current_index = -1

    # PLAYLIST MANAGEMENT ---
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select audio files",
            os.path.expanduser("~"),
            "Audio Files (*.mp3 *.wav *.ogg *.m4a *.flac)"
        )

        for f in files:
            self.playlist.append({"path": f, "title": os.path.basename(f)})
            self.list_widget.addItem(os.path.basename(f))

        if self.current_index == -1 and self.playlist:
            self.current_index = 0

    def remove_selected(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)
            del self.playlist[row]

            if row == self.current_index:
                self.stop()
                self.current_index = -1

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.shuffle_btn.setText(f"Shuffle: {'On' if self.shuffle else 'Off'}")

    def toggle_repeat(self):
        self.repeat = not self.repeat
        self.repeat_btn.setText(f"Repeat: {'On' if self.repeat else 'Off'}")

    # VOLUME + SEEK ---
    def set_volume(self, value):
        self.player.volume = value

    def seek_position(self):
        if self.player.duration:
            new_pos = self.progress.value() / 1000
            self.player.seek(new_pos, reference="absolute-percent")

    # DISPLAY ---
    def update_time_label(self):
        try:
            pos = self.player.time_pos or 0
            dur = self.player.duration or 0
            self.time_label.setText(f"{self.format_time(pos)} / {self.format_time(dur)}")
        except:
            pass

    @staticmethod
    def format_time(sec):
        sec = int(sec)
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


# START APP ---
def main():
    app = QApplication(sys.argv)
    win = MPVStreamerPlayer()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
