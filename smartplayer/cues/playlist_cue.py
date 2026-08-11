from __future__ import annotations

from .cue import Cue, CueState, CueAction
from ..core.properties import Property
from .media import Media


class PlaylistItem:
    def __init__(self):
        self.uri = ""
        self.name = ""
        self.duration = 0
        self.fade_in = 500
        self.fade_out = 500

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "duration": self.duration,
            "fade_in": self.fade_in,
            "fade_out": self.fade_out,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PlaylistItem:
        item = cls()
        item.uri = data.get("uri", "")
        item.name = data.get("name", "")
        item.duration = data.get("duration", 0)
        item.fade_in = data.get("fade_in", 500)
        item.fade_out = data.get("fade_out", 500)
        return item


class PlaylistCue(Cue):
    _type_ = Property(default="PlaylistCue")
    items_json = Property(default=[])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._items: list[PlaylistItem] = []
        self._current_item_index = 0
        self._item_player = None
        self._item_audio = None

    @property
    def items(self) -> list[PlaylistItem]:
        return self._items

    def add_item(self, uri: str):
        import os
        item = PlaylistItem()
        item.uri = uri
        item.name = os.path.basename(uri)
        self._items.append(item)
        self.items_json = [i.to_dict() for i in self._items]

    def remove_item(self, index: int):
        if 0 <= index < len(self._items):
            self._items.pop(index)
            self.items_json = [i.to_dict() for i in self._items]

    def _do_start(self):
        self._current_item_index = 0
        self._play_next_item()

    def set_video_output(self, video_widget):
        self._video_output = video_widget

    def _play_next_item(self):
        if self._current_item_index >= len(self._items):
            self._do_stop()
            return

        item = self._items[self._current_item_index]
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PySide6.QtCore import QUrl

        if self._item_player is None:
            self._item_player = QMediaPlayer()
            self._item_audio = QAudioOutput()
            self._item_player.setAudioOutput(self._item_audio)
            self._item_player.mediaStatusChanged.connect(self._on_item_status)

        if hasattr(self, '_video_output') and self._video_output:
            self._item_player.setVideoOutput(self._video_output)

        self._item_player.setSource(QUrl.fromLocalFile(item.uri))
        self._item_player.play()
        self.state = CueState.Running

    def _on_item_status(self, status):
        from PySide6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._current_item_index += 1
            self._play_next_item()

    def _do_stop(self):
        if self._item_player is not None:
            self._item_player.stop()
        super()._do_stop()

    def _do_pause(self):
        if self._item_player is not None:
            self._item_player.pause()
        super()._do_pause()

    def _do_resume(self):
        if self._item_player is not None:
            self._item_player.play()
        super()._do_resume()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["items"] = [i.to_dict() for i in self._items]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> PlaylistCue:
        items_data = data.pop("items", [])
        cue = super().from_dict(data)
        cue._items = [PlaylistItem.from_dict(d) for d in items_data]
        return cue
