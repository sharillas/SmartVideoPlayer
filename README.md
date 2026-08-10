# SmartVideoPlayer

**Cue player for stage productions — Windows edition**

SmartVideoPlayer is a professional cue-based media player designed for theater, musicals, live events, and stage productions. Built from scratch for Windows.

---

## Features

### Core
- **Cue-based playback** — trigger media cues with precise timing
- **5 Next Actions** — Next Cue, Previous Cue, Stop at end & out, Pause and keep Last Frame, Loop
- **Fade In / Fade Out** — 5 fade curves: Linear, Quadratic, Exponential, Logarithmic, SCurve


### Media Support
- **Audio**: WAV, MP3, OGG, FLAC, AAC, M4A, WMA
- **Video**: MP4, AVI, MKV, MOV, WMV, WebM, M4V, MPG, MPEG, FLV, 3GP
- **Hardware-accelerated decoding** via Windows Media Foundation / FFmpeg

### Video Output
- **External Display** — auto-detects secondary monitor, opens fullscreen black
- **Separate Window** — standalone 800x600 window when no external display
- **Display ON/OFF** — toggle video output without stopping playback
- **Fullscreen toggle** — F / F11 in video window, Esc to close
- **Stop at end & out** — fades out and hides video
- **Pause and keep Last Frame** — pauses on last frame, video stays visible

### UI
- **Minimalist dark theme** — professional interface optimized for low-light environments
- **Split layout** — cue table (left) + inline editor panel (right)
- **Real-time progress bar** — green badge fill on the "Remaining" column during playback
- **State indicators** — color-coded rows (green=running, yellow=paused, blue=prewait)
- **Keyboard shortcuts** — Space=GO, Esc=Stop, Ctrl+Z=Undo, Ctrl+Y=Redo
- **Cue columns**: Cue | Name | Remaining | Duration | Next

### Session Management
- **Save/Load** — JSON-based `.sps` session files
- **Auto-save** — quick SAVE button in the editor panel
- **New / Open / Save As** — full file management

### Cue Types
| Type | Description |
|---|---|
| **MediaCue** | Audio and video playback with loop, start/stop time, volume |
| **CommandCue** | Executes shell commands |
| **StopAllCue** | Stops all running cues |
| **CollectionCue** | Triggers multiple cues simultaneously |

---

## Architecture

```
smartplayer/
├── main.py                 # Entry point + dark theme
├── core/
│   ├── signal.py           # Custom signal/slot system
│   ├── properties.py       # Property descriptor with change notification
│   ├── has_properties.py   # Mixin for property-based objects
│   ├── configuration.py    # JSON configuration files (read/write)
│   └── fader.py            # Fade curves + Fader timer
├── cues/
│   ├── cue.py              # Cue base class (state machine, actions, NextAction enum)
│   ├── media.py            # Media object (uri, loop, volume, start/stop)
│   ├── media_cue.py        # MediaCue with QMediaPlayer backend
│   ├── cue_model.py        # OrderedDict-based cue container
│   ├── cue_factory.py      # Registry pattern for cue types
│   ├── command_cue.py      # Shell command cue
│   ├── stop_all_cue.py     # Stop-all cue
│   └── collection_cue.py   # Multi-cue trigger
└── ui/
    ├── mainwindow.py       # Main window + menus (File, Edit, Settings)
    ├── cue_list_view.py    # Cue table + controls + video output
    ├── cue_table_model.py  # QAbstractTableModel + ProgressDelegate
    ├── cue_editor_panel.py # Right-side inline editor (Cue Settings / Fade / Media tabs)
    ├── cue_settings.py     # Legacy popup dialog (kept for reference)
    ├── session.py          # Session save/load (JSON .sps)
    ├── video_output_window.py  # External display / separate window
    ├── video_output_manager.py # Auto-detect screens, manage output mode
    ├── display_settings.py # Display configuration dialog
    ├── undo_stack.py       # Undo/Redo command stack
    └── cue_list_model.py   # Legacy model (kept for reference)
```

### Tech Stack
- **Python 3.9+**
- **PySide6** (Qt 6) — UI framework
- **Qt Multimedia** — native Windows playback (QMediaPlayer + QAudioOutput + QVideoWidget)

### Cue State Machine
```
                    ┌─────────────────────────────┐
                    │         Start                │
                    │   (PreWait if pre_wait>0)    │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │         Running              │
                    │  ┌─────────┐ ┌─────────────┐ │
                    │  │  Pause   │ │  Fade In/Out │ │
                    │  └────┬─────┘ └─────────────┘ │
                    └───────┼───────────────────────┘
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
          StopEndOut   PauseKeepLast   Loop
          (fade out)   (pause frame)   (restart)
```

---

## Installation

### Option 1: Run from source

```powershell
# Clone
git clone https://github.com/sharillas/SmartVideoPlayer.git
cd SmartVideoPlayer

# Install dependencies
pip install -r requirements.txt

# Run
python run.py
```

### Option 2: Compiled executable (Windows)

Download `SmartVideoPlayer.exe` from [Releases](https://github.com/sharillas/SmartVideoPlayer/releases).

Run directly — no Python required.

---

## Build from source

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name SmartVideoPlayer --icon=NONE run.py
```

Output: `dist/SmartVideoPlayer.exe`

---

## Usage

```powershell
python run.py                     # Launch app
python run.py -f session.sps      # Open session file
python run.py --version           # Show version
```

### Keyboard Shortcuts
| Key | Action |
|---|---|
| **Space** | GO (trigger selected cue) |
| **Esc** | STOP current cue |
| **Ctrl+Z** | Undo |
| **Ctrl+Y** | Redo |
| **F / F11** | Toggle video fullscreen (in video window) |

### Mouse
| Action | Result |
|---|---|
| **Click** cue row | Select cue, show editor panel |
| **+ ADD** | Add media files |
| **DEL** | Remove selected cue |
| **GO** | Play selected cue |
| **STOP** | Stop selected cue |
| **PAUSE** | Pause/Resume selected cue |
| **ALL OFF** | Stop all cues |

---

## Session File Format (.sps)

```json
{
  "meta": { "version": "0.1.0" },
  "session": { "layout_type": "ListLayout" },
  "cues": [
    {
      "_type_": "MediaCue",
      "id": "uuid",
      "name": "Intro",
      "fadein_duration": 3000,
      "fadeout_duration": 3000,
      "fadein_type": "Linear",
      "fadeout_type": "Linear",
      "next_action": "NextCue",
      "media": {
        "uri": "C:/media/intro.mp4",
        "loop": false,
        "volume": 80,
        "start_time": 0,
        "stop_time": 0
      }
    }
  ]
}
```

---

## License

GPLv3 — see [LICENSE](LICENSE)
