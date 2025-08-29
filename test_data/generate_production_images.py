#!/usr/bin/env python3
"""Generate production-style 1920x1080 test images matching Silverstack CSV."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import csv
import random

def create_production_image(filename: str, scene: str, shot: str, take: str, 
                          camera: str, fps: str, resolution: str = "1920x1080"):
    """Create a production-style test image with metadata overlay."""
    
    # Parse resolution
    width, height = map(int, resolution.split('x'))
    
    # Generate a unique color based on scene/camera
    random.seed(f"{scene}{camera}")
    base_color = (
        random.randint(40, 100),
        random.randint(40, 100), 
        random.randint(40, 100)
    )
    
    # Create image
    img = Image.new('RGB', (width, height), color=base_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a monospace font for production look
    try:
        # Try different font options
        font_large = ImageFont.truetype("Courier New.ttf", 72)
        font_medium = ImageFont.truetype("Courier New.ttf", 48)
        font_small = ImageFont.truetype("Courier New.ttf", 32)
    except:
        try:
            font_large = ImageFont.truetype("DejaVuSansMono.ttf", 72)
            font_medium = ImageFont.truetype("DejaVuSansMono.ttf", 48)
            font_small = ImageFont.truetype("DejaVuSansMono.ttf", 32)
        except:
            # Fallback to default
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Add film grain texture
    for _ in range(5000):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        brightness = random.randint(-20, 20)
        pixel_color = tuple(max(0, min(255, c + brightness)) for c in base_color)
        img.putpixel((x, y), pixel_color)
    
    # Add production slate info
    slate_info = [
        f"SCENE: {scene}",
        f"SHOT: {shot}",
        f"TAKE: {take}",
        f"CAMERA: {camera}",
        f"FPS: {fps}"
    ]
    
    # Draw slate background (top area)
    slate_bg = Image.new('RGBA', (width, 200), (0, 0, 0, 180))
    img.paste(slate_bg, (0, 0), slate_bg)
    
    # Draw slate text
    y_pos = 20
    for line in slate_info:
        draw.text((50, y_pos), line, fill=(255, 255, 255), font=font_small)
        y_pos += 35
    
    # Add large clip name in center
    clip_name = Path(filename).stem
    text_bbox = draw.textbbox((0, 0), clip_name, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Center position
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw shadow
    draw.text((x+3, y+3), clip_name, fill=(0, 0, 0), font=font_large)
    # Draw main text
    draw.text((x, y), clip_name, fill=(255, 255, 255), font=font_large)
    
    # Add frame guides (action safe / title safe)
    # Action safe (90%)
    action_margin_x = int(width * 0.05)
    action_margin_y = int(height * 0.05)
    draw.rectangle(
        [action_margin_x, action_margin_y, 
         width - action_margin_x, height - action_margin_y],
        outline=(100, 100, 100), width=1
    )
    
    # Title safe (80%)
    title_margin_x = int(width * 0.1)
    title_margin_y = int(height * 0.1)
    draw.rectangle(
        [title_margin_x, title_margin_y,
         width - title_margin_x, height - title_margin_y],
        outline=(80, 80, 80), width=1
    )
    
    # Add corner markers
    marker_size = 50
    marker_color = (255, 255, 0)
    marker_width = 3
    
    # Top-left
    draw.line([(0, 0), (marker_size, 0)], fill=marker_color, width=marker_width)
    draw.line([(0, 0), (0, marker_size)], fill=marker_color, width=marker_width)
    
    # Top-right
    draw.line([(width - marker_size, 0), (width, 0)], fill=marker_color, width=marker_width)
    draw.line([(width, 0), (width, marker_size)], fill=marker_color, width=marker_width)
    
    # Bottom-left
    draw.line([(0, height), (marker_size, height)], fill=marker_color, width=marker_width)
    draw.line([(0, height - marker_size), (0, height)], fill=marker_color, width=marker_width)
    
    # Bottom-right
    draw.line([(width - marker_size, height), (width, height)], fill=marker_color, width=marker_width)
    draw.line([(width, height - marker_size), (width, height)], fill=marker_color, width=marker_width)
    
    # Add timecode burn-in (bottom)
    tc_bg = Image.new('RGBA', (width, 60), (0, 0, 0, 180))
    img.paste(tc_bg, (0, height - 60), tc_bg)
    
    # Simulate timecode
    tc_text = f"01:00:00:00  |  {clip_name}  |  {resolution} @ {fps}fps"
    draw.text((50, height - 40), tc_text, fill=(255, 255, 255), font=font_small)
    
    # Save
    output_path = Path(__file__).parent / filename
    img.save(output_path, 'JPEG', quality=95)
    print(f"Created: {output_path}")
    return output_path


def main():
    """Generate test images from Silverstack CSV."""
    
    csv_file = Path(__file__).parent / "silverstack_production.csv"
    
    if not csv_file.exists():
        print(f"Error: {csv_file} not found")
        return
    
    # Read CSV and generate unique images
    generated_files = set()
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Generate filename from clip name
            clip_name = row['Clip Name']
            filename = f"{clip_name}.jpg"
            
            # Skip if already generated
            if filename in generated_files:
                continue
            
            # Extract metadata
            scene = row.get('Scene', 'N/A')
            shot = row.get('Shot', '1')
            take = row.get('Take', '1')
            camera = row.get('Camera', 'Unknown')
            fps = row.get('FPS', '23.976')
            
            # For this test, always create 1920x1080 for consistency
            resolution = "1920x1080"
            
            # Create the image
            create_production_image(
                filename, scene, shot, take,
                camera, fps, resolution
            )
            
            generated_files.add(filename)
    
    print(f"\n[SUCCESS] Generated {len(generated_files)} production test images")
    print("Images are 1920x1080 to match standard proxy resolution")
    print("\nYou can now test with:")
    print("  python -m src.slatelink.app")
    print("  Load any of the generated images")
    print("  Load silverstack_production.csv")
    print("  The app will match images to CSV rows by Clip Name")


if __name__ == '__main__':
    main()