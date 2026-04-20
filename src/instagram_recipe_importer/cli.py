"""
Instagram Recipe Importer - CLI Tool

Extract recipe information from Instagram and YouTube posts.
"""

from pathlib import Path
from datetime import datetime

import click

from .extractor import RecipeExtractor


def echo_step(message: str) -> None:
    click.echo(f"{message}...", err=True)


def echo_success(message: str) -> None:
    click.echo(f"Success: {message}", err=True)


def echo_error(message: str) -> None:
    click.echo(f"Error: {message}", err=True)


def echo_created_file(path: str) -> None:
    click.echo(f"Created: {path}", err=True)


def echo_extractor_error(extractor: RecipeExtractor, fallback: str) -> None:
    echo_error(extractor.last_error or fallback)


def echo_processed_files(extractor: RecipeExtractor) -> None:
    if not extractor.created_files:
        return

    click.echo("", err=True)
    click.echo("Processed files:", err=True)
    for path in extractor.created_files:
        click.echo(f"- {path}", err=True)


def validate_url(ctx, param, value):
    """Validate that the URL is an Instagram or YouTube URL."""
    if not value:
        return value
    
    url_lower = value.lower()
    if (
        'instagram.com' not in url_lower
        and 'youtube.com' not in url_lower
        and 'youtu.be' not in url_lower
    ):
        raise click.BadParameter(
            "URL must be an Instagram or YouTube URL "
            "(containing 'instagram.com', 'youtube.com', or 'youtu.be')"
        )
    return value


@click.command()
@click.argument("url", callback=validate_url)
@click.option(
    "--output-dir",
    type=str,
    default=None,
    help=(
        "Output directory for extracted files. "
        "Defaults to /tmp/insta_recipe_<timestamp>"
    )
)
@click.option(
    "--caption-only",
    is_flag=True,
    default=False,
    help="Only extract caption/description, skip video download and processing"
)
@click.option(
    "--no-thumbnail",
    is_flag=True,
    default=False,
    help="Skip downloading thumbnail image"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output"
)
def main(url, output_dir, caption_only, no_thumbnail, verbose):
    """Extract recipe information from an Instagram or YouTube post.
    
    URL should be a post/video URL containing a recipe.
    
    Examples:
        insta-recipe https://www.instagram.com/p/ABC123/
        insta-recipe https://www.youtube.com/watch?v=ABC123
        insta-recipe https://youtu.be/ABC123
    """
    # Determine output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"/tmp/insta_recipe_{timestamp}"
    
    output_path = Path(output_dir)
    
    if verbose:
        click.echo(f"Output directory: {output_path}", err=True)
    
    # Create extractor
    extractor = RecipeExtractor(str(output_path))
    
    results = {
        "caption": False,
        "video_download": None,
        "transcription": False,
        "ocr": False,
        "thumbnail": None,
    }
    
    # Step 1: Extract caption
    echo_step("Extracting caption/description")
    results["caption"] = extractor.extract_caption(url)
    caption_path = extractor.get_output_path("captions.txt")
    if results["caption"]:
        echo_success(f"Caption saved to {caption_path}.")
    else:
        echo_extractor_error(extractor, "Failed to extract caption.")
        if Path(caption_path).exists():
            echo_created_file(caption_path)
    
    # If caption-only mode, we're done
    if caption_only:
        click.echo("", err=True)
        click.echo(f"Output saved to: {output_path}", err=True)
        echo_processed_files(extractor)
        return
    
    # Step 2: Download video
    click.echo("", err=True)
    echo_step("Downloading video")
    video_path = extractor.download_video(url)
    if video_path:
        results["video_download"] = video_path
        echo_success(f"Video downloaded to {video_path}.")
    else:
        echo_extractor_error(
            extractor,
            "Failed to download video (may be image-only post)."
        )
    
    # Step 3: Transcribe audio (if video exists)
    if video_path:
        click.echo("", err=True)
        echo_step("Transcribing audio")
        results["transcription"] = extractor.transcribe_audio(video_path)
        transcription_path = extractor.get_output_path("transcription.txt")
        if results["transcription"]:
            echo_success(f"Audio transcription saved to {transcription_path}.")
        else:
            echo_extractor_error(extractor, "Failed to transcribe audio.")
            if Path(transcription_path).exists():
                echo_created_file(transcription_path)
    
    # Step 4: OCR on video frames (if video exists)
    if video_path:
        click.echo("", err=True)
        echo_step("Running OCR on video frames")
        results["ocr"] = extractor.extract_text_ocr(video_path)
        ocr_path = extractor.get_output_path("ocr.txt")
        if results["ocr"]:
            echo_success(f"OCR results saved to {ocr_path}.")
        else:
            echo_extractor_error(extractor, "Failed to run OCR.")
            if Path(ocr_path).exists():
                echo_created_file(ocr_path)
    
    # Step 5: Download thumbnail
    if not no_thumbnail:
        click.echo("", err=True)
        echo_step("Downloading thumbnail")
        thumbnail_path = extractor.download_thumbnail(url)
        if thumbnail_path:
            results["thumbnail"] = thumbnail_path
            echo_success(f"Thumbnail downloaded to {thumbnail_path}.")
        else:
            echo_extractor_error(extractor, "Failed to download thumbnail.")
    
    # Summary
    click.echo("\n" + "="*50, err=True)
    click.echo("Extraction Summary", err=True)
    click.echo("="*50, err=True)
    click.echo(f"Output directory: {output_path}", err=True)
    click.echo(f"Caption extracted: {'yes' if results['caption'] else 'no'}", err=True)
    if not caption_only:
        click.echo(
            f"Video downloaded: {'yes' if results['video_download'] else 'no'}",
            err=True
        )
        click.echo(
            f"Audio transcribed: {'yes' if results.get('transcription') else 'no'}",
            err=True
        )
        click.echo(f"OCR completed: {'yes' if results.get('ocr') else 'no'}", err=True)
    thumbnail_status = (
        "skipped" if no_thumbnail else "yes" if results.get("thumbnail") else "no"
    )
    click.echo(f"Thumbnail downloaded: {thumbnail_status}", err=True)
    echo_processed_files(extractor)
    click.echo("="*50, err=True)


if __name__ == "__main__":
    main()
