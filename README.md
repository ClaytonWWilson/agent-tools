# Instagram Recipe Importer

A CLI tool that extracts recipe information from **Instagram** and **YouTube** posts, including:
- **Captions/Descriptions** - Text content from post descriptions or video descriptions
- **Audio Transcription** - Whisper-based transcription of narrated recipes
- **OCR** - Text extraction from video frames (for visual/text-overlay recipes)
- **Thumbnail Download** - Cover image extraction

## Installation

### Using uv (recommended)

```bash
# Install from local directory
uv tool install .

# Or install directly from a git repository
uv tool install git+https://github.com/yourusername/instagram-recipe-importer.git
```

### Using pip

```bash
pip install .
```

## Usage

### Basic Usage - Instagram

```bash
insta-recipe "https://www.instagram.com/p/ABC123/"
```

### Basic Usage - YouTube

```bash
# Full URL
insta-recipe "https://www.youtube.com/watch?v=ABC123"

# Shortened youtu.be URL
insta-recipe "https://youtu.be/ABC123"
```

The tool **auto-detects** the platform from the URL.

This will:
1. Extract the caption → `/tmp/insta_recipe_<timestamp>/captions.txt`
2. Download the video (if present)
3. Transcribe audio → `/tmp/insta_recipe_<timestamp>/transcription.txt`
4. Run OCR on frames → `/tmp/insta_recipe_<timestamp>/ocr.txt`
5. Download thumbnail → `/tmp/insta_recipe_<timestamp>/thumbnail.jpg`

### Options

```bash
# Only extract caption (skip video processing)
insta-recipe "URL" --caption-only

# Use custom output directory
insta-recipe "URL" --output-dir /my/custom/path

# Skip thumbnail download
insta-recipe "URL" --no-thumbnail

# Verbose output
insta-recipe "URL" -v
```

### Output Files

All files are saved to `/tmp/insta_recipe_<timestamp>/` by default:

| File | Description |
|------|-------------|
| `captions.txt` | Post caption/description text |
| `transcription.txt` | Whisper transcription of audio |
| `ocr.txt` | Text extracted from video frames |
| `thumbnail.jpg` | Cover image/thumbnail |

### Example Output

```bash
$ insta-recipe "https://www.instagram.com/p/ABC123/" -v
📁 Output directory: /tmp/insta_recipe_20240115_143022
📝 Extracting caption...
✅ Caption extracted

🎬 Downloading video...
✅ Video downloaded: /tmp/insta_recipe_20240115_143022/video_ABC123.mp4

🎤 Transcribing audio...
✅ Audio transcribed

👁️ Running OCR on video frames...
✅ OCR completed

🖼️ Downloading thumbnail...
✅ Thumbnail downloaded: /tmp/insta_recipe_20240115_143022/thumbnail.jpg

==================================================
📊 Extraction Summary
==================================================
Output directory: /tmp/insta_recipe_20240115_143022
Caption extracted: ✅
Video downloaded: ✅
Audio transcribed: ✅
OCR completed: ✅
Thumbnail downloaded: ✅
==================================================
```

## Dependencies

- **yt-dlp** - Video/caption extraction from Instagram
- **faster-whisper** - Audio transcription
- **easyocr** - OCR on video frames
- **opencv-python-headless** - Video frame processing
- **click** - CLI framework

### Installing System Dependencies (if needed)

For Whisper and OCR to work properly, you may need:

```bash
# Ubuntu/Debian
sudo apt-get install libsndfile1

# macOS
brew install sndfile
```

## Error Handling

If any extraction method fails, an error message is written to the corresponding output file instead of leaving it empty. This makes it easy to detect failures programmatically.

### Example Error Output

```text
# captions.txt (on failure)
No caption found in post metadata

# transcription.txt (on failure)  
No audio detected or no speech transcribed

# ocr.txt (on failure)
No text found via OCR
```

## Programmatic Usage

You can also use the extractor directly in Python:

```python
from instagram_recipe_importer import InstagramExtractor

extractor = InstagramExtractor("/tmp/my_output")

# Extract caption
extractor.extract_caption("https://www.instagram.com/p/ABC123/")

# Download video and process
video_path = extractor.download_video("https://www.instagram.com/p/ABC123/")
if video_path:
    extractor.transcribe_audio(video_path)
    extractor.extract_text_ocr(video_path)
```

## License

MIT License - See LICENSE file for details.
