"""
Instagram Recipe Extractor

Core extraction logic for captions, audio transcription, and OCR.
"""

import glob
import json
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class RecipeExtractor:
    """Extract recipe information from Instagram and YouTube posts."""
    
    def __init__(self, output_dir: str):
        """Initialize extractor with output directory.
        
        Args:
            output_dir: Directory to save extracted files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.last_error: Optional[str] = None
        self.created_files: list[str] = []

    def _get_whisper_device(self) -> Tuple[str, str]:
        """Return the fastest available faster-whisper device settings."""
        try:
            import ctranslate2

            if ctranslate2.get_cuda_device_count() > 0:
                return "cuda", "float16"
        except Exception:
            pass

        return "cpu", "int8"

    def _torch_cuda_available(self) -> bool:
        """Return whether PyTorch can use CUDA in this environment."""
        try:
            import torch

            return torch.cuda.is_available()
        except Exception:
            return False

    def _get_app_cache_dir(self) -> Path:
        """Return the cache directory owned by this tool."""
        if env_cache_dir := os.environ.get("INSTAGRAM_RECIPE_IMPORTER_CACHE_DIR"):
            cache_dir = Path(env_cache_dir).expanduser()
        elif xdg_cache_home := os.environ.get("XDG_CACHE_HOME"):
            cache_dir = (
                Path(xdg_cache_home).expanduser() / "instagram-recipe-importer"
            )
        else:
            cache_dir = Path.home() / ".cache" / "instagram-recipe-importer"

        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(
                f"Unable to create cache directory at {cache_dir}: {e}"
            ) from e

        return cache_dir

    def _get_whisper_download_root(self) -> str:
        """Return a writable model cache for faster-whisper downloads."""
        download_root = self._get_app_cache_dir() / "faster-whisper"
        try:
            download_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(
                f"Unable to create Whisper cache at {download_root}: {e}"
            ) from e

        return str(download_root)

    def _detect_source(self, url: str) -> str:
        """Auto-detect the source platform from URL.
        
        Args:
            url: The video/post URL
            
        Returns:
            'instagram' or 'youtube'
        """
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        else:
            raise ValueError(
                f"Unsupported URL: {url}. "
                f"Must be from Instagram or YouTube."
            )
    
    def extract_caption(self, url: str) -> bool:
        """Extract caption/description from post.
        
        Args:
            url: Post URL (Instagram or YouTube)
            
        Returns:
            True if successful, False otherwise
        """
        self._clear_error()
        try:
            # Detect source platform
            source = self._detect_source(url)
            
            cmd = [
                "yt-dlp", "--dump-json", url,
                "--no-warnings", "--quiet"
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )
            
            if result.returncode != 0:
                error_detail = (
                    result.stderr.strip()
                    or result.stdout.strip()
                    or "yt-dlp failed while loading post metadata"
                )
                error_msg = f"yt-dlp failed: {error_detail}"
                self._record_error(error_msg)
                self._write_to_file("captions.txt", error_msg)
                return False
            
            data = json.loads(result.stdout)
            
            # Platform-specific extraction
            if source == "youtube":
                # YouTube: title + description (recipe often in description)
                title = data.get("title", "")
                description = data.get("description", "")
                
                output_lines = []
                if title:
                    output_lines.append(f"TITLE: {title}")
                if description:
                    output_lines.append("")
                    output_lines.append("DESCRIPTION:")
                    # Truncate very long descriptions
                    max_length = 10000
                    if len(description) > max_length:
                        description = description[:max_length] + "\n... [truncated]"
                    output_lines.append(description)
                
                caption_text = "\n".join(output_lines).strip()
            else:  # instagram
                # Instagram: caption/description fields
                caption = (
                    data.get("description", "") or
                    data.get("full_description", "") or
                    data.get("title", "") or
                    ""
                )
                
                if not caption:
                    error_msg = "No caption found in post metadata"
                    self._record_error(error_msg)
                    self._write_to_file("captions.txt", error_msg)
                    return False
                
                # Truncate very long captions
                max_length = 10000
                if len(caption) > max_length:
                    caption = caption[:max_length] + "\n... [truncated]"
                
                caption_text = caption
            
            self._write_to_file("captions.txt", caption_text)
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse yt-dlp output: {e}"
            self._record_error(error_msg)
            self._write_to_file("captions.txt", error_msg)
            return False
        except ValueError as e:
            error_msg = str(e)
            self._record_error(error_msg)
            self._write_to_file("captions.txt", error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error extracting caption: {e}"
            self._record_error(error_msg)
            self._write_to_file("captions.txt", error_msg)
            return False
    
    def download_video(self, url: str) -> Optional[str]:
        """Download video from post.
        
        Args:
            url: Post URL (Instagram or YouTube)
            
        Returns:
            Path to downloaded video file, or None if failed
        """
        self._clear_error()
        try:
            self._detect_source(url)
            output_path = self.output_dir / "video.mp4"
            
            # Prefer H.264/AVC so OpenCV can decode frames reliably for OCR.
            format_str = (
                "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/"
                "best[ext=mp4][vcodec^=avc1]/"
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                "best[ext=mp4]/best"
            )
            
            cmd = [
                "yt-dlp",
                "-f", format_str,
                "--output", str(output_path),
                "--merge-output-format", "mp4",
                "--no-warnings",
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                self._record_error(
                    result.stderr.strip()
                    or result.stdout.strip()
                    or "yt-dlp failed to download video"
                )
                return None
            
            if output_path.exists():
                self._record_created_file(output_path)
                return str(output_path)

            # yt-dlp can still append an extension in some edge cases.
            files = glob.glob(str(self.output_dir / "video.*"))
            
            if not files:
                self._record_error(
                    "yt-dlp completed but no downloaded video file was found"
                )
                return None

            self._record_created_file(files[0])
            return files[0]
            
        except Exception as e:
            self._record_error(f"Error downloading video: {e}")
            return None
    
    def transcribe_audio(self, video_path: str) -> bool:
        """Transcribe audio from video using Whisper.
        
        Args:
            video_path: Path to downloaded video
            
        Returns:
            True if successful, False otherwise
        """
        self._clear_error()
        try:
            from faster_whisper import WhisperModel

            device, compute_type = self._get_whisper_device()
            download_root = self._get_whisper_download_root()
            try:
                model = WhisperModel(
                    "small",
                    device=device,
                    compute_type=compute_type,
                    download_root=download_root,
                )
            except Exception:
                if device != "cuda":
                    raise
                model = WhisperModel(
                    "small",
                    device="cpu",
                    compute_type="int8",
                    download_root=download_root,
                )

            segments, _ = model.transcribe(
                video_path,
                beam_size=5,
                language="en"
            )
            
            transcription_lines = []
            for segment in segments:
                timestamp = f"[{segment.start:.2f}-{segment.end:.2f}]"
                transcription_lines.append(f"{timestamp} {segment.text}")
            
            if not transcription_lines:
                error_msg = "No audio detected or no speech transcribed"
                self._record_error(error_msg)
                self._write_to_file("transcription.txt", error_msg)
                return False
            
            transcription_text = "\n".join(transcription_lines)
            self._write_to_file("transcription.txt", transcription_text)
            return True
            
        except ImportError:
            error_msg = (
                "faster-whisper not installed. "
                "Install with: pip install faster-whisper"
            )
            self._record_error(error_msg)
            self._write_to_file("transcription.txt", error_msg)
            return False
        except Exception as e:
            error_msg = f"Transcription failed: {e}"
            self._record_error(error_msg)
            self._write_to_file("transcription.txt", error_msg)
            return False
    
    def extract_text_ocr(self, video_path: str) -> bool:
        """Extract text from video frames using OCR.
        
        Args:
            video_path: Path to downloaded video
            
        Returns:
            True if successful, False otherwise
        """
        self._clear_error()
        cleanup_video_path: Optional[str] = None
        try:
            import cv2
            from easyocr import Reader

            ocr_video_path, cleanup_video_path = self._prepare_video_for_ocr(
                video_path
            )
            cap = cv2.VideoCapture(ocr_video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_rate = max(1, int(frame_count / 30))
            frames = []
            
            for i in range(0, frame_count, sample_rate):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            cap.release()
            
            if not frames:
                error_msg = "No frames could be read from video"
                self._record_error(error_msg)
                self._write_to_file("ocr.txt", error_msg)
                return False
            
            # EasyOCR uses PyTorch for GPU acceleration.
            try:
                reader = Reader(['en', 'de'], gpu=self._torch_cuda_available())
            except Exception:
                reader = Reader(['en', 'de'], gpu=False)
            
            all_text = set()
            for frame in frames:
                result = reader.readtext(frame, detail=0)
                if result:
                    for text in result:
                        if len(text.strip()) > 2:
                            all_text.add(text.strip().upper())
            
            if not all_text:
                error_msg = "No text found via OCR"
                self._record_error(error_msg)
                self._write_to_file("ocr.txt", error_msg)
                return False
            
            ocr_output = "TEXT FOUND:\n" + "\n".join(sorted(all_text))
            self._write_to_file("ocr.txt", ocr_output)
            return True
            
        except ImportError as e:
            missing = "opencv-python-headless" if "cv2" in str(e) else "easyocr"
            error_msg = (
                f"{missing} not installed. "
                f"Install with: pip install {missing} opencv-python-headless"
            )
            self._record_error(error_msg)
            self._write_to_file("ocr.txt", error_msg)
            return False
        except Exception as e:
            error_msg = f"OCR failed: {e}"
            self._record_error(error_msg)
            self._write_to_file("ocr.txt", error_msg)
            return False
        finally:
            if cleanup_video_path:
                Path(cleanup_video_path).unlink(missing_ok=True)

    def _prepare_video_for_ocr(self, video_path: str) -> Tuple[str, Optional[str]]:
        """Return a video path OpenCV can read, plus an optional cleanup path."""
        codec = self._get_video_codec(video_path)
        if codec.lower() == "av1":
            transcoded_path = self._transcode_video_for_ocr(video_path)
            return transcoded_path, transcoded_path

        return video_path, None

    def _get_video_codec(self, video_path: str) -> str:
        """Read the first video stream codec name with ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                "ffprobe is required to inspect video codec before OCR"
            ) from e

        if result.returncode != 0:
            error_detail = (
                result.stderr.strip()
                or result.stdout.strip()
                or "unknown ffprobe error"
            )
            raise RuntimeError(f"ffprobe failed before OCR: {error_detail}")

        output = result.stdout.strip()
        codec = output.splitlines()[0] if output else ""
        if not codec:
            raise RuntimeError("ffprobe did not find a video stream for OCR")

        return codec

    def _transcode_video_for_ocr(self, video_path: str) -> str:
        """Transcode AV1 video to an H.264 copy for OpenCV frame reads."""
        with tempfile.NamedTemporaryFile(
            dir=self.output_dir,
            prefix="ocr_",
            suffix=".mp4",
            delete=False,
        ) as temp_file:
            output_path = temp_file.name

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", video_path,
            "-map", "0:v:0",
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            output_path,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )
        except FileNotFoundError as e:
            Path(output_path).unlink(missing_ok=True)
            raise RuntimeError(
                "ffmpeg is required to transcode AV1 video for OCR"
            ) from e

        if result.returncode != 0:
            Path(output_path).unlink(missing_ok=True)
            error_detail = (
                result.stderr.strip()
                or result.stdout.strip()
                or "unknown ffmpeg error"
            )
            raise RuntimeError(
                f"ffmpeg failed while transcoding AV1 video for OCR: {error_detail}"
            )

        return output_path
    
    def download_thumbnail(self, url: str) -> Optional[str]:
        """Download thumbnail/image from post.
        
        Args:
            url: Post URL (Instagram or YouTube)
            
        Returns:
            Path to downloaded image, or None if failed
        """
        self._clear_error()
        try:
            # Detect source platform
            source = self._detect_source(url)
            
            cmd = ["yt-dlp", "--dump-json", url, "--no-warnings", "--quiet"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                self._record_error(
                    result.stderr.strip()
                    or result.stdout.strip()
                    or "yt-dlp failed while loading thumbnail metadata"
                )
                return None
            
            data = json.loads(result.stdout)
            
            # Platform-specific thumbnail extraction
            image_url = None
            
            if source == "youtube":
                # YouTube: extract video ID and construct thumbnail URL
                video_id = data.get("id")
                if video_id:
                    # maxresdefault = 1280x720, sddefault = 640x480
                    image_url = (
                        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    )
            else:  # instagram
                entry = data.get("entries", [{}])[0] if "entries" in data else data
                
                # Try different thumbnail fields
                if "thumbnail" in entry:
                    image_url = entry["thumbnail"]
                elif "thumbnails" in entry and entry["thumbnails"]:
                    thumbnails = sorted(
                        entry["thumbnails"],
                        key=lambda x: x.get("width", 0) * x.get("height", 0),
                        reverse=True
                    )
                    image_url = thumbnails[0]["url"] if thumbnails else None
                elif "video_thumbnail" in entry:
                    image_url = entry["video_thumbnail"]
            
            if not image_url:
                self._record_error("No thumbnail URL found in post metadata")
                return None
            
            # Download image
            import urllib.request
            output_path = self.output_dir / "thumbnail.jpg"
            urllib.request.urlretrieve(image_url, str(output_path))
            self._record_created_file(output_path)
            
            return str(output_path)
            
        except Exception as e:
            self._record_error(f"Error downloading thumbnail: {e}")
            return None

    def get_output_path(self, filename: str) -> str:
        """Return the absolute output path for a generated file."""
        return str(self.output_dir / filename)

    def _clear_error(self) -> None:
        self.last_error = None

    def _record_error(self, message: str) -> None:
        self.last_error = message

    def _record_created_file(self, filepath: str | Path) -> None:
        path = str(filepath)
        if path not in self.created_files:
            self.created_files.append(path)
    
    def _write_to_file(self, filename: str, content: str) -> None:
        """Write content to a file in the output directory.
        
        Args:
            filename: Name of the file
            content: Content to write
        """
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        self._record_created_file(filepath)
