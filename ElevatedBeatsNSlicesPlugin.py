from pathlib import Path
from typing import Optional

from UM.Extension import Extension
from cura.CuraApplication import CuraApplication
from UM.Backend.Backend import BackendState
from UM.i18n import i18nCatalog
from UM.Logger import Logger

from PyQt6.QtCore import QUrl, QTimer, pyqtSlot
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import QFileDialog

from UM.Message import Message

catalog = i18nCatalog("cura")
DEFAULT_MP3 = str(Path(__file__).parent.joinpath("resources/waiting-music-116216.mp3"))


class ElevatedBeatsNSlicesPlugin(Extension):
    def __init__(self):
        super().__init__()
        self._backend = None
        self._player = None
        self._audio_output = None
        self._fader_speed = 50
        self._error_message: Optional[Message] = None  # Pop-up message that shows errors.
        self._application = CuraApplication.getInstance()
        self._application.engineCreatedSignal.connect(self._onEngineCreated)
        self._preferences = self._application.getPreferences()
        self._preferences.addPreference("elevated_beats_n_slices/source_mp3", DEFAULT_MP3)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Select MP3"), self.selectSourceMP3)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Default"), self.backToDefault)

    def _onEngineCreated(self):
        self._backend = CuraApplication.getInstance().getBackend()
        self._backend.backendStateChange.connect(self._onBackendStateChange)
        self._backend.slicingCancelled.connect(self._stopPlaying)
        self._backend.backendError.connect(self._stopPlaying)

    def handle_media_error(self, mediaError):
        error_dict = {
            QMediaPlayer.NoError: "NoError - No error has occurred.",
            QMediaPlayer.ResourceError: "ResourceError - A media resource couldn't be resolved.",
            QMediaPlayer.FormatError: "FormatError - The format of a media resource isn't supported.",
            QMediaPlayer.NetworkError: "NetworkError - A network error occurred.",
            QMediaPlayer.AccessDeniedError: "AccessDeniedError - There are not the necessary permissions to play a media resource.",
            QMediaPlayer.ServiceMissingError: "ServiceMissingError -  A valid playback service was not found.",
            QMediaPlayer.MediaIsPlaylist: "MediaIsPlaylist - Media is a playlist."
        }

        err_code = mediaError.error()
        err_message = mediaError.errorString()

        self._error_message = Message(catalog.i18nc("@info:status",
                                                    f"An error occurred in QMediaPlayer: {error_dict.get(err_code, str(err_code))}\nError Message: {err_message}\n\nPlease report this error to the plugin developer.."),
                                      title = catalog.i18nc("@info:title", "Elevated Beats 'n' Slices Error"),
                                      message_type = Message.MessageType.ERROR)
        self._error_message.show()
        Logger.error(f"An error occurred in QMediaPlayer: {error_dict.get(err_code, str(err_code))}, Error Message: {err_message}")

    def _stopPlaying(self):
        Logger.debug("Fading out")
        self._fadeInTimer.stop()  # Stop the fade-in timer
        self._fadeOutTimer = QTimer()
        self._fadeOutTimer.timeout.connect(self._fadeout)
        self._fadeOutTimer.start(self._fader_speed)  # Every 50 ms the volume will be lowered

    def _onBackendStateChange(self, state):
        if state == BackendState.Processing:
            Logger.info("Starting to play music")
            try:
                self._player = QMediaPlayer()
                Logger.debug(f"QMediaPlayer initialized")
                self._player.errorOccurred.connect(self.handle_media_error)
            except Exception as e:
                self._error_message = Message(catalog.i18nc("@info:status",
                                                            f"QMediaPlayer could not be initialized: {str(e)}\n\nPlease report this error to the plugin developer."),
                                              title = catalog.i18nc("@info:title", "Elevated Beats 'n' Slices Error"),
                                              message_type = Message.MessageType.ERROR)
                self._error_message.show()
                Logger.error(f"QMediaPlayer could not be initialized: {str(e)}")
                return
            Logger.debug(f"Setting up audio output")
            self._audio_output = QAudioOutput()
            music_path = self._preferences.getValue("elevated_beats_n_slices/source_mp3")
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
            self._stopPlaying()

    def _fadeout(self):
        if self._player is None:
            return
        volume = self._player.audioOutput().volume()
        if volume <= 0.0:  # when volume is 0, stop the music and timer
            self._player.stop()
            self._player = None
            self._audio_output = None
            self._fadeOutTimer.stop()
        else:
            self._player.audioOutput().setVolume(volume - 0.01)  # decrease volume

    def _fadein(self):
        if self._player is None:
            return
        volume = self._player.audioOutput().volume()
        if volume >= 1.0:  # when volume is 1, stop the timer
            self._fadeInTimer.stop()
        else:
            self._player.audioOutput().setVolume(volume + 0.01)  # increase volume

    @pyqtSlot()
    def selectSourceMP3(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Select MP3 File", "", "MP3 Files (*.mp3)")
        if file_path:
            self._preferences.setValue("elevated_beats_n_slices/source_mp3", file_path)

    @pyqtSlot()
    def backToDefault(self):
        self._preferences.setValue("elevated_beats_n_slices/source_mp3", DEFAULT_MP3)
