---
name: mealie-recipe-importer
description: This skill enables importing recipes from Instagram posts and youtube videos into Mealie.
license: Complete terms in LICENSE.txt
---

# Recipe Importer Skill

## Overview

This skill enables importing recipes from Instagram posts and Youtube videos into Mealie by extracting recipe information through multiple methods:

1. **Caption** - Most reliable method for text-based recipes
2. **Whisper Transcription** - For audio-narrated recipes
3. **Video Frame OCR** - For visual/text-overlay recipes

## Prerequisites

- yt-dlp installed: `pip install yt-dlp`
- faster-whisper installed: `pip install faster-whisper`
- easyocr installed: `pip install easyocr opencv-python-headless`
- Mealie MCP server configured with valid API credentials

## Workflow Steps

### Step 1: Use the social-content-extract command to extract the video data

```bash
social-content-extract <INSTAGRAM_OR_YOUTUBE_URL>
```

Extracted data will be printed after completion

### Step 2: Parse Recipe Information From Outputs

Outputs should be saved into a /tmp/ folder, so read those and look for the following

Extract from the gathered text:

- **Recipe Name**: Usually first line or title
- **Ingredients**: Look for Ingredients sections with quantities
- **Instructions**: Look for Instructions sections
- **Servings**: Look for servings
- **Time**: Look for time mentions like "15 minutes"

### Step 3: Create Recipe in Mealie

```python
# Use the mealie_create_recipe tool
mealie_create_recipe(
    name="Recipe Name",
    ingredients=["ingredient 1", "ingredient 2", ...],
    instructions=["step 1", "step 2", ...]
)
```

### Step 4: Add Description and Metadata

```python
# Use mealie_patch_recipe to add details
mealie_patch_recipe(
    slug="recipe-slug",
    description="Description with original link",
    recipe_yield="X servings",
    total_time="XX minutes"
)
```

Ensure that the original instagram/youtube url is linked in the recipe

### Step 5 (REQUIRED): Upload the Recipe Image

# Download image from Instagram

Use the image downloaded from the social-content-extract tool and upload it to the mealie recipe

# Upload recipe image to Mealie via the mealie_upload_recipe_image_file tool

mealie_upload_recipe_image_file [slug=viral-crispy-rice-salad-salmon-version, image_path=/tmp/placeholder-food.jpg]

## Before Finishing - Verify:

1. Recipe created with ingredients and instructions? ✅
2. Description includes original Instagram/Youtube URL? ✅
3. Image uploaded successfully? ✅
4. Response to user confirms all components added? ✅

## Quick Reference: Tool Calls

```python
# Create recipe
mealie_create_recipe(name="...", ingredients=[...], instructions=[...])

# Update metadata
mealie_patch_recipe(slug="...", description="...", recipe_yield="...", total_time="...")

# Set image from URL (if direct image link)
mealie_set_recipe_image_from_url(slug="...", image_url="...")

# Upload image file
mealie_upload_recipe_image_file(slug="...", image_path="...")
```
