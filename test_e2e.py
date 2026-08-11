import sys
import os
import logging
import traceback

sys.path.insert(0, os.path.dirname(__file__))

# Setup logging
log_file = os.path.join(os.path.dirname(__file__), "test_log.txt")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

log.info("=" * 60)
log.info("SmartPlayer End-to-End Test")
log.info("=" * 60)

# Step 1: Import modules
log.info("Step 1: Importing modules...")
try:
    from smartplayer.core.signal import Signal
    from smartplayer.core.properties import Property
    from smartplayer.core.has_properties import HasProperties
    from smartplayer.cues.cue import Cue, CueState, CueAction, NextAction
    from smartplayer.cues.media import Media
    from smartplayer.cues.media_cue import MediaCue
    from smartplayer.cues.cue_model import CueModel
    from smartplayer.cues.cue_factory import CueFactory
    from smartplayer.ui.video_output_window import VideoOutputWindow
    from smartplayer.ui.video_output_manager import VideoOutputManager
    log.info("  All imports OK")
except Exception as e:
    log.error(f"  Import failed: {e}")
    log.error(traceback.format_exc())
    sys.exit(1)

# Step 2: Cue creation
log.info("Step 2: Creating test cues...")
cue_model = CueModel()
test_files = [
    r"E:\Pasta Arquivo\Conteudos de Teste\1__16067_EventoASF_SALA_INTRO.mp4",
    r"E:\Pasta Arquivo\Conteudos de Teste\BG_Loop_H.264 MP4 - 3240x1080.mp4",
    r"E:\Pasta Arquivo\Conteudos de Teste\Smart Logo.mov",
    r"E:\Pasta Arquivo\Conteudos de Teste\Soluções ecommerce CTT Loop2.mov",
]
for f in test_files:
    if os.path.exists(f):
        cue = MediaCue()
        cue.name = os.path.basename(f)
        cue.media.uri = f
        cue.media.file_size = os.path.getsize(f)
        cue.fadein_duration = 3000
        cue.fadeout_duration = 500
        cue.output_target = 1
        cue_model.add(cue)
        log.info(f"  Added: {cue.name} ({cue.media.file_size/1024/1024:.1f}MB)")
    else:
        log.warning(f"  File not found: {f}")

log.info(f"  Total cues: {len(cue_model)}")

# Step 3: Test Cue actions (without GUI)
log.info("Step 3: Testing cue state machine...")
for cue in cue_model.cues():
    log.info(f"  Cue: {cue.name}")
    log.info(f"    Initial state: {cue.state}")
    cue.execute(CueAction.Start)
    log.info(f"    After start: {cue.state}")
    cue.execute(CueAction.Pause)
    log.info(f"    After pause: {cue.state}")
    cue.execute(CueAction.Resume)
    log.info(f"    After resume: {cue.state}")
    cue.execute(CueAction.Stop)
    log.info(f"    After stop: {cue.state}")

# Step 4: Test session save/load
log.info("Step 4: Testing session save/load...")
from smartplayer.ui.session import Session
session = Session()
for cue in cue_model.cues():
    session.cue_model.add(cue)
test_path = "test_session.sps"
session.save(test_path)
log.info(f"  Saved to {test_path}")

session2 = Session()
if session2.load(test_path):
    log.info(f"  Loaded OK: {len(session2.cue_model)} cues")
else:
    log.error("  Load failed!")

# Step 5: Test mpv availability
log.info("Step 5: Testing mpv...")
mpv_exe = "C:/Program Files/MPV Player/mpv.exe"
if os.path.exists(mpv_exe):
    log.info(f"  mpv found at: {mpv_exe}")
    import subprocess
    try:
        result = subprocess.run([mpv_exe, '--version'], capture_output=True, text=True, timeout=5)
        log.info(f"  mpv version: {result.stdout.split(chr(10))[0]}")
    except Exception as e:
        log.error(f"  mpv launch failed: {e}")
else:
    log.error(f"  mpv NOT FOUND at {mpv_exe}")

# Step 6: Check for issues
log.info("Step 6: Checking for known issues...")
issues = []

# Check if _on_media_status and _on_position_changed are needed
if hasattr(MediaCue, '_on_media_status'):
    issues.append("MediaCue._on_media_status exists but mpv doesn't use it")
if hasattr(MediaCue, '_on_position_changed'):
    issues.append("MediaCue._on_position_changed exists but mpv doesn't use it")

# Check if PlayerLoop is handled
for cue in cue_model.cues():
    if cue.next_action == NextAction.Loop:
        log.info(f"  Loop cue: {cue.name} - mpv will handle via loop-file=inf")

for issue in issues:
    log.warning(f"  {issue}")

log.info("=" * 60)
log.info("TEST COMPLETE")
log.info(f"Log saved to: {log_file}")
log.info("=" * 60)
