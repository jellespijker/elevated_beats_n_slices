from pathlib import Path

from UM.Extension import Extension
from cura.CuraApplication import CuraApplication
from UM.Backend.Backend import BackendState
from UM.i18n import i18nCatalog

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

catalog = i18nCatalog("cura")


class ElevatedBeatsNSlicesPlugin(Extension):
    def __init__(self):
        super().__init__()
        self._backend = None
        self._player = None
        self._audio_output = None
        CuraApplication.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

    def _onEngineCreated(self):
        self._backend = CuraApplication.getInstance().getBackend()
        self._backend.backendStateChange.connect(self._onBackendStateChange)

    def _onBackendStateChange(self, state):
        if state == BackendState.Processing:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setSource(QUrl.fromLocalFile(str(Path(__file__).parent.joinpath("resources/waiting-music-116216.mp3"))))
            self._player.setAudioOutput(self._audio_output)
            self._player.setLoops(-1)
            self._player.audioOutput().setVolume(1.0)
            self._player.play()
        elif state == BackendState.Done or state == BackendState.Error:
            self._player.stop()
            self._player = None
            self._audio_output = None
