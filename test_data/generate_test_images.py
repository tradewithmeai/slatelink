#!/usr/bin/env python3
"""Generate test JPEG images for testing the application."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_test_image(filename: str, text: str, color: tuple = (100, 150, 200)):
    """Create a test JPEG image with text."""
    # Create image
    img = Image.new('RGB', (800, 600), color=color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    # Add text
    text_width = draw.textlength(text, font=font)
    text_height = 50  # Approximate
    x = (800 - text_width) // 2
    y = (600 - text_height) // 2
    
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    
    # Add filename at bottom
    draw.text((10, 570), filename, fill=(255, 255, 255))
    
    # Save
    output_path = Path(__file__).parent / filename
    img.save(output_path, 'JPEG', quality=95)
    print(f"Created: {output_path}")


def main():
    """Generate test images matching the CSV data."""
    test_images = [
        ("IMG_0001.jpg", "Scene 12B - Take 3", (100, 120, 140)),
        ("IMG_0002.jpg", "Scene 12B - Take 4", (120, 100, 140)),
        ("IMG_0003.jpg", "Scene 12C - Take 1", (140, 100, 120)),
        ("IMG_0004.jpg", "Scene 12C - Take 2", (100, 140, 120)),
        ("IMG_0005.jpg", "Scene 13A - Take 1", (120, 140, 100)),
    ]
    
    for filename, text, color in test_images:
        create_test_image(filename, text, color)
    
    print("\nTest images created successfully!")
    print("CSV file already exists: test_metadata.csv")
    print("\nYou can now run the main app with: python ../app.py")


if __name__ == '__main__':
    main()