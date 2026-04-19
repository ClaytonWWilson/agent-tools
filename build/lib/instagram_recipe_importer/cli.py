"""
Instagram Recipe Importer - CLI Tool

Extract recipe information from Instagram and YouTube posts.
"""

from pathlib import Path
from datetime import datetime

import click

from .extractor import RecipeExtractor


def validate_url(ctx, param, value):
    """Validate that the URL is an Instagram or YouTube URL."""
    if not value:
        return value

    url_lower = value.lower()
    if (
        "instagram.com" not in url_lower
        and "youtube.com" not in url_lower
        and "youtu.be" not in url_lower
    ):
        raise click.BadParameter(
            "URL must be an Instagram or YouTube URL (containing 'instagram.com', 'youtube.com', or 'youtu.be')"
        )
    return value


@click.command()
@click.argument("url", callback=validate_url)
@click.option(
    "--output-dir",
    type=str,
    default=None,
    help="Output directory for extracted files. Defaults to /tmp/insta_recipe_<timestamp>",
)
@click.option(
    "--caption-only",
    is_flag=True,
    default=False,
    help="Only extract caption/description, skip video download and processing",
)
@click.option(
    "--no-thumbnail",
    is_flag=True,
    default=False,
    help="Skip downloading thumbnail image",
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Enable verbose output"
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
        click.echo(f"📁 Output directory: {output_path}", err=True)

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
    click.echo("📝 Extracting caption/description...", err=True)
    results["caption"] = extractor.extract_caption(url)
    if results["caption"]:
        click.echo("✅ Caption extracted", err=True)
    else:
        click.echo("❌ Failed to extract caption", err=True)

    # If caption-only mode, we're done
    if caption_only:
        click.echo(f"\n📦 Output saved to: {output_path}", err=True)
        return

    # Step 2: Download video
    click.echo("\n🎬 Downloading video...", err=True)
    video_path = extractor.download_video(url)
    if video_path:
        results["video_download"] = video_path
        click.echo(f"✅ Video downloaded: {video_path}", err=True)
    else:
        click.echo("❌ Failed to download video (may be image-only post)", err=True)

    # Step 3: Transcribe audio (if video exists)
    if video_path:
        click.echo("\n🎤 Transcribing audio...", err=True)
        results["transcription"] = extractor.transcribe_audio(video_path)
        if results["transcription"]:
            click.echo("✅ Audio transcribed", err=True)
        else:
            click.echo("❌ Failed to transcribe audio", err=True)

    # Step 4: OCR on video frames (if video exists)
    if video_path:
        click.echo("\n👁️ Running OCR on video frames...", err=True)
        results["ocr"] = extractor.extract_text_ocr(video_path)
        if results["ocr"]:
            click.echo("✅ OCR completed", err=True)
        else:
            click.echo("❌ Failed to run OCR", err=True)

    # Step 5: Download thumbnail
    if not no_thumbnail:
        click.echo("\n🖼️ Downloading thumbnail...", err=True)
        thumbnail_path = extractor.download_thumbnail(url)
        if thumbnail_path:
            results["thumbnail"] = thumbnail_path
            click.echo(f"✅ Thumbnail downloaded: {thumbnail_path}", err=True)
        else:
            click.echo("❌ Failed to download thumbnail", err=True)

    # Summary
    click.echo("\n" + "=" * 50, err=True)
    click.echo("📊 Extraction Summary", err=True)
    click.echo("=" * 50, err=True)
    click.echo(f"Output directory: {output_path}", err=True)
    click.echo(f"Caption extracted: {'✅' if results['caption'] else '❌'}", err=True)
    if not caption_only:
        click.echo(
            f"Video downloaded: {'✅' if results['video_download'] else '❌'}", err=True
        )
        click.echo(
            f"Audio transcribed: {'✅' if results.get('transcription') else '❌'}",
            err=True,
        )
        click.echo(f"OCR completed: {'✅' if results.get('ocr') else '❌'}", err=True)
    click.echo(
        f"Thumbnail downloaded: {'✅' if results.get('thumbnail') else '❌'}", err=True
    )
    click.echo("=" * 50, err=True)


if __name__ == "__main__":
    main()
