# Social Content Extractor

A CLI tool that extracts content information from **Instagram** and **YouTube** posts, including:

- **Descriptions** - Text content from post descriptions or video descriptions
- **Audio Transcription** - Whisper-based transcription of spoken audio
- **OCR** - Text extraction from video frames
- **Thumbnail Download** - Cover image extraction

## Installation

### Using uv (recommended)

```bash
# Install from local directory
uv tool install .

# Or install directly from a git repository
uv tool install git+https://github.com/yourusername/social-content-extractor.git
```

### Using pip

```bash
pip install .
```

## Usage

### Basic Usage - Instagram

```bash
social-content-extract "https://www.instagram.com/p/ABC123/"
```

### Basic Usage - YouTube

```bash
# Full URL
social-content-extract "https://www.youtube.com/watch?v=ABC123"

# Shortened youtu.be URL
social-content-extract "https://youtu.be/ABC123"
```

The tool **auto-detects** the platform from the URL.

This will:

1. Extract the description → `/tmp/social_content_<timestamp>/description.txt`
2. Download the video (if present)
3. Transcribe audio → `/tmp/social_content_<timestamp>/transcription.txt`
4. Run OCR on frames → `/tmp/social_content_<timestamp>/ocr.txt`
5. Download thumbnail → `/tmp/social_content_<timestamp>/thumbnail.jpg`

### Options

```bash
# Only extract description text (skip video processing)
social-content-extract "URL" --description-only

# Use custom output directory
social-content-extract "URL" --output-dir /my/custom/path

# Skip thumbnail download
social-content-extract "URL" --no-thumbnail

# Verbose output
social-content-extract "URL" -v
```

### Output Files

All files are saved to `/tmp/social_content_<timestamp>/` by default:

| File                | Description                      |
| ------------------- | -------------------------------- |
| `description.txt`   | Post description text            |
| `transcription.txt` | Whisper transcription of audio   |
| `ocr.txt`           | Text extracted from video frames |
| `thumbnail.jpg`     | Cover image/thumbnail            |

### Example Output

```bash
$ social-content-extract "https://www.instagram.com/p/ABC123/" -v
Output directory: /tmp/social_content_20240115_143022
Extracting description text...
Success: Description saved to /tmp/social_content_20240115_143022/description.txt.

Downloading video...
Success: Video downloaded to /tmp/social_content_20240115_143022/video.mp4.

Transcribing audio...
Success: Audio transcription saved to /tmp/social_content_20240115_143022/transcription.txt.

Running OCR on video frames...
Success: OCR results saved to /tmp/social_content_20240115_143022/ocr.txt.

Downloading thumbnail...
Success: Thumbnail downloaded to /tmp/social_content_20240115_143022/thumbnail.jpg.

==================================================
Extraction Summary
==================================================
Output directory: /tmp/social_content_20240115_143022
Description extracted: yes
Video downloaded: yes
Audio transcribed: yes
OCR completed: yes
Thumbnail downloaded: yes

Processed files:
- /tmp/social_content_20240115_143022/description.txt
- /tmp/social_content_20240115_143022/video.mp4
- /tmp/social_content_20240115_143022/transcription.txt
- /tmp/social_content_20240115_143022/ocr.txt
- /tmp/social_content_20240115_143022/thumbnail.jpg
==================================================
```

## Dependencies

- **yt-dlp** - Video and description extraction from supported platforms `uv tool install yt-dlp`
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

If any extraction method fails, the error is printed to the terminal. When a text
output file can be created for that step, the same error message is written to
the corresponding output file instead of leaving it empty. This makes it easy to
detect failures programmatically.

### Example Error Output

```text
# description.txt (on failure)
No description found in post metadata

# transcription.txt (on failure)
No audio detected or no speech transcribed

# ocr.txt (on failure)
No text found via OCR
```

## Programmatic Usage

You can also use the extractor directly in Python:

```python
from social_content_extractor import ContentExtractor

extractor = ContentExtractor("/tmp/my_output")

# Extract description text
extractor.extract_description("https://www.instagram.com/p/ABC123/")

# Download video and process
video_path = extractor.download_video("https://www.instagram.com/p/ABC123/")
if video_path:
    extractor.transcribe_audio(video_path)
    extractor.extract_ocr_text(video_path)
```

## License

MIT License - See LICENSE file for details.
