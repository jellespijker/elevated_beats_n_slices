from pathlib import Path

from UM.Extension import Extension
from cura.CuraApplication import CuraApplication
from UM.Backend.Backend import BackendState
from UM.i18n import i18nCatalog
from UM.Logger import Logger

from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

catalog = i18nCatalog("cura")


class ElevatedBeatsNSlicesPlugin(Extension):
    def __init__(self):
        super().__init__()
        self._backend = None
        self._player = None
        self._audio_output = None
        self._fader_speed = 50
        CuraApplication.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

    def _onEngineCreated(self):
        self._backend = CuraApplication.getInstance().getBackend()
        self._backend.backendStateChange.connect(self._onBackendStateChange)

    def _onBackendStateChange(self, state):
        if state == BackendState.Processing:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            music_path = str(Path(__file__).parent.joinpath("resources/waiting-music-116216.mp3"))
            Logger.debug(f"Playing {music_path}")
            self._player.setSource(QUrl.fromLocalFile(music_path))
            self._player.setAudioOutput(self._audio_output)
            self._player.setLoops(-1)
            self._player.audioOutput().setVolume(0.0)  # set initial volume to 0
            self._fadeInTimer = QTimer()
            self._fadeInTimer.timeout.connect(self._fadein)
            self._fadeInTimer.start(self._fader_speed)  # Every 50 ms the volume will be increased
            self._player.play()
        elif state == BackendState.Done or state == BackendState.Error:
            Logger.debug("Fading out")
            self._fadeInTimer.stop()  # Stop the fade-in timer
            self._fadeOutTimer = QTimer()
            self._fadeOutTimer.timeout.connect(self._fadeout)
            self._fadeOutTimer.start(self._fader_speed)  # Every 50 ms the volume will be lowered

    def _fadeout(self):
        volume = self._player.audioOutput().volume()
        if volume <= 0.0:  # when volume is 0, stop the music and timer
            self._player.stop()
            self._player = None
            self._audio_output = None
            self._fadeOutTimer.stop()
        else:
            self._player.audioOutput().setVolume(volume - 0.01)  # decrease volume

    def _fadein(self):
        volume = self._player.audioOutput().volume()
        if volume >= 1.0:  # when volume is 1, stop the timer
            self._fadeInTimer.stop()
        else:
            self._player.audioOutput().setVolume(volume + 0.01)  # increase volume