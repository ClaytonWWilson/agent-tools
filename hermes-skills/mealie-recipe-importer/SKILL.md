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

- **yt-dlp** - Video and description extraction from supported platforms `uv tool install yt-dlp`
- **faster-whisper** - Audio transcription
- **easyocr** - OCR on video frames
- **opencv-python-headless** - Video frame processing
- **click** - CLI framework

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

```bash
# Use the mealie binary in the hermes bin folder. It contains the create-recipe tool
mealie create-recipe \
  --name "Recipe Name" \
  --ingredients '["ingredient 1", "ingredient 2"]' \
  --instructions '["step 1", "step 2"]'
```

### Step 4: Add Description and Metadata

```bash
# Use patch-recipe to add details
mealie patch-recipe \
  --slug "recipe-slug" \
  --description "Description with original link" \
  --recipe-yield "X servings" \
  --total-time "XX minutes"
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

```bash
# Create recipe
mealie create-recipe --name "..." --ingredients '[...]' --instructions '[...]'

# Update metadata
mealie patch-recipe --slug "..." --description "..." --recipe-yield "..." --total-time "..."

# Upload image file
mealie upload-recipe-image-file --slug "..." --image-path "..."

```
