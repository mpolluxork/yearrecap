# Year in 365 Seconds

Automatically generate a video recap of your 2025 year, with each day represented by 1-1.5 seconds of photos or videos.

## Features

- 📅 **Smart date detection** - Compares filename vs metadata, chooses most reliable
- 💾 **Intelligent caching** - Reuses processed clips for instant regeneration
- 🔄 **Resume capability** - Continue from where you left off after interruption
- 🎨 **Date validation UI** - Review and correct dates with visual interface
- 🎬 **Ken Burns effects** on static photos for cinematic feel
- 📊 **Visual calendar reports** showing coverage
- 🎥 **Smart video processing** with random clip extraction
- 🎞️ **Month separators** with elegant transitions (in Spanish)
- 📦 **All media types supported**: JPG, PNG, HEIC, GIF, MP4, MOV
- 🎵 **Audio soundtrack** - Add music from YouTube with crossfades between months

## Quick Start

### Prerequisites

1. **Install FFmpeg** - [Download here](https://ffmpeg.org/download.html)
   - Verify installation: `ffmpeg -version`

2. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

### Usage

#### One Command to Rule Them All 🎬

Simply run:

```powershell
python generate_recap_optimized.py
```

This single command will:
1. ✅ Scan your media folder and detect new/changed files (incremental)
2. ✅ Assign files to days based on smart date detection
3. ✅ Generate the complete video with Ken Burns effects and date captions
4. ✅ Cache processed clips for faster regeneration
5. ✅ Save checkpoint to resume if interrupted (Ctrl+C, power loss)

**Output:**
- `output/2025_recap.mp4` - Your final video (silent)
- `output/2025_recap_with_audio.mp4` - Your final video with music!
- `output/month_XX_Month.mp4` - Individual monthly videos
- `report_visual.txt` - Calendar showing coverage
- `report_detailed.csv` - Spreadsheet with all assignments

#### Features

- **Smart Caching**: Unchanged files reuse processed clips (instant)
- **Resume Capability**: Interrupted? Just run again to continue
- **Date Validation UI**: Run `python media_validator_app.py` to review/correct dates

#### Advanced: Run Steps Separately (Optional)

If you want to run the steps manually:

**Step 1: Assign Media to Days**
```powershell
python assign_media.py
```

**Step 2: Generate Video**
```powershell
python generate_video.py
```

## Configuration

Edit `config.py` to customize:

- **Video settings**: Resolution, quality, FPS
- **Durations**: Photo (1s), Video (1.5s), GIF (1.5s max)
- **Ken Burns effect**: Zoom range, easing
- **Month separators**: Colors, fonts, duration

## Project Structure

```
yearrecap/
├── Recap 2025/              # 📁 INPUT: Your media files go here
├── output/                  # 📁 OUTPUT: Final videos
│   ├── month_01_Enero.mp4
│   ├── month_02_Febrero.mp4
│   ├── 2025_recap.mp4           # Your final video (silent)
│   └── 2025_recap_with_audio.mp4 # Your final video with music
├── audio/                   # 📁 AUDIO: Downloaded MP3s for soundtrack
├── processed/               # 📁 CACHE: Processed clips (kept for speed)
├── templates/               # 📁 UI templates (for date validator)
├── utils_and_tests/         # 📁 Test scripts and deprecated utilities
│   ├── test_*.py           # Test scripts
│   └── generate_*.py       # Old/deprecated scripts
├── generate_recap_optimized.py  # ⭐ MAIN SCRIPT - Run this!
├── download_audio.py        # 🎵 Download audio from YouTube
├── add_audio_to_recap.py    # 🎵 Add soundtrack to video
├── media_validator_app.py   # 🎨 UI to review/correct dates
├── assign_media.py          # Core: Media assignment
├── generate_optimized.py    # Core: Video generation
├── generate_video.py        # Core: Video processing
├── checkpoint.py            # Core: Resume functionality
├── incremental_scan.py      # Core: Change detection
├── config.py                # 🔧 Configuration
├── utils.py                 # 🔧 Helper functions
├── requirements.txt         # 📦 Python dependencies
├── urls.txt                 # 🎵 YouTube URLs for audio (one per month)
├── media_assignment.json    # 📄 Date assignments
└── checkpoint.json          # 📄 Resume state
```

## Media Files

Place all your 2025 photos and videos in the `Recap 2025/` folder. Supported formats:

- **Images**: JPG, PNG, HEIC (Apple), GIF
- **Videos**: MP4, MOV, AVI, MKV

The script will:
1. Extract dates from EXIF metadata
2. Parse dates from filenames (e.g., `20250102_161334.jpg`)
3. Fall back to file modification date

## Duration Logic

- **Photos**: 1 second each (with Ken Burns zoom effect)
- **Videos**: 1.5 seconds each (random clip extracted)
- **GIFs**: Respects animation, max 1.5 seconds
- **Multiple media per day**: All included, in chronological order

## Tips

- **Check coverage**: Review `report_visual.txt` to see which days need media
- **Quality**: Higher resolution originals = better final video
- **Testing**: The final video will be 6-10 minutes for ~250 days of coverage
- **Re-run anytime**: Safe to run scripts multiple times

## Troubleshooting

**"FFmpeg not found"**
- Install FFmpeg and ensure it's in your system PATH

**"pillow-heif not found" or HEIC errors**
- Run: `pip install pillow-heif`

**Wrong year assigned**
- Check that EXIF dates are correct
- Script uses filename dates as priority

**Video too short/long**
- Adjust `PHOTO_DURATION` and `VIDEO_DURATION` in `config.py`

## Adding Audio Soundtrack 🎵

After generating your video, you can add a music soundtrack with a different song for each month:

### Step 1: Choose Your Songs

Edit `urls.txt` and add 12 YouTube URLs (one per line, one per month):

```
https://www.youtube.com/watch?v=SONG_FOR_JANUARY
https://www.youtube.com/watch?v=SONG_FOR_FEBRUARY
... (12 URLs total)
```

### Step 2: Download Audio

**Prerequisite**: Install yt-dlp:
```bash
pip install yt-dlp
```

Then download the audio:
```bash
python download_audio.py
```

This downloads each URL as `01.mp3`, `02.mp3`, ... `12.mp3` in the `audio/` folder.

### Step 3: Add Audio to Video

```bash
python add_audio_to_recap.py
```

This will:
- Extract a random segment from each month's MP3 matching the video duration
- Apply crossfades between monthly segments
- Add fade in/out at the beginning and end
- Create `output/2025_recap_with_audio.mp4`

---

Enjoy your 2025 video recap! 🎉
