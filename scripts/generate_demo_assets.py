#!/usr/bin/env python3
"""
Generate demo assets for SlateLink testing.
Creates synthetic JPEG images and a Silverstack-style CSV file.
"""

import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os


def create_gradient_image(width: int, height: int, name: str, colors: tuple) -> Image.Image:
    """Create a simple gradient image with text label."""
    # Create base image with gradient
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient from top-left color to bottom-right color
    for y in range(height):
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * y / height)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * y / height)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add text label
    try:
        # Try to use a reasonable font size
        font_size = min(width, height) // 20
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    text_bbox = draw.textbbox((0, 0), name, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    # Draw text with black outline for visibility
    for offset in [(1,1), (1,-1), (-1,1), (-1,-1)]:
        draw.text((text_x + offset[0], text_y + offset[1]), name, font=font, fill=(0, 0, 0))
    draw.text((text_x, text_y), name, font=font, fill=(255, 255, 255))
    
    return img


def generate_demo_images():
    """Generate demo JPEG images."""
    test_data_dir = Path('test_data')
    test_data_dir.mkdir(exist_ok=True)
    
    # Image specifications
    images = [
        ('IMG_0001.jpg', ((100, 150, 200), (200, 100, 150))),  # Blue to pink gradient
        ('IMG_0002.jpg', ((150, 200, 100), (100, 200, 150))),  # Green gradient  
        ('IMG_0003.jpg', ((200, 150, 100), (150, 100, 200))),  # Orange to purple gradient
    ]
    
    for filename, colors in images:
        image_path = test_data_dir / filename
        name = filename.replace('.jpg', '')
        
        img = create_gradient_image(1920, 1080, name, colors)
        img.save(image_path, 'JPEG', quality=85)
        print(f"Created: {image_path}")


def generate_demo_csv():
    """Generate Silverstack-style CSV with film metadata."""
    test_data_dir = Path('test_data')
    test_data_dir.mkdir(exist_ok=True)
    
    csv_path = test_data_dir / 'exampleFilmMetadata.csv'
    
    # Silverstack-style headers (based on exampleFilmMetadata.csv)
    headers = [
        'Camera', 'Name', 'Bin Name', 'Episode', 'Scene', 'Take', 'Duration', 
        'File Size', 'EI/ISO (ASA)', 'White Balance', 'Tint', 'Resolution', 
        'Project FPS', 'Sensor Fps', 'Shutter', 'Shutter Angle', 'Lens Model', 
        'Focal Length', 'T-Stop', 'ND Filter', 'Focus Distance', 'Codec', 
        'File Type', 'Registration Date', 'TC Start', 'TC End', 'Shooting Day', 
        'Verified Backups'
    ]
    
    # Demo data rows
    rows = [
        {
            'Camera': 'A Cam',
            'Name': 'IMG_0001.jpg',
            'Bin Name': 'Demo_001',
            'Episode': '1',
            'Scene': '1A',
            'Take': '1',
            'Duration': '10.5',
            'File Size': '8472640',
            'EI/ISO (ASA)': '800',
            'White Balance': '5600',
            'Tint': '0',
            'Resolution': '1920x1080',
            'Project FPS': '24.00',
            'Sensor Fps': '24.00',
            'Shutter': '1/48s',
            'Shutter Angle': '180.0° @ 24fps',
            'Lens Model': 'Demo 50mm',
            'Focal Length': '50',
            'T-Stop': '2.8',
            'ND Filter': '',
            'Focus Distance': '3.5',
            'Codec': 'JPEG',
            'File Type': 'jpg',
            'Registration Date': '2025-01-15 12:00:00 +0000',
            'TC Start': '01:00:00:00',
            'TC End': '01:00:10:12',
            'Shooting Day': '001',
            'Verified Backups': '1'
        },
        {
            'Camera': 'B Cam',
            'Name': 'IMG_0002.jpg', 
            'Bin Name': 'Demo_002',
            'Episode': '1',
            'Scene': '1A',
            'Take': '2',
            'Duration': '8.25',
            'File Size': '7841280',
            'EI/ISO (ASA)': '800',
            'White Balance': '5600',
            'Tint': '0',
            'Resolution': '1920x1080',
            'Project FPS': '24.00',
            'Sensor Fps': '24.00',
            'Shutter': '1/48s',
            'Shutter Angle': '180.0° @ 24fps',
            'Lens Model': 'Demo 85mm',
            'Focal Length': '85',
            'T-Stop': '4.0',
            'ND Filter': '0.6',
            'Focus Distance': '5.2',
            'Codec': 'JPEG',
            'File Type': 'jpg',
            'Registration Date': '2025-01-15 12:01:00 +0000',
            'TC Start': '01:00:15:00',
            'TC End': '01:00:23:06',
            'Shooting Day': '001',
            'Verified Backups': '1'
        },
        {
            'Camera': 'C Cam',
            'Name': 'IMG_0003.jpg',
            'Bin Name': 'Demo_003', 
            'Episode': '1',
            'Scene': '2B',
            'Take': '1',
            'Duration': '12.75',
            'File Size': '9216000',
            'EI/ISO (ASA)': '1600',
            'White Balance': '3200',
            'Tint': '-10',
            'Resolution': '1920x1080',
            'Project FPS': '24.00',
            'Sensor Fps': '24.00',
            'Shutter': '1/48s', 
            'Shutter Angle': '180.0° @ 24fps',
            'Lens Model': 'Demo 24mm',
            'Focal Length': '24',
            'T-Stop': '1.4',
            'ND Filter': '',
            'Focus Distance': '2.1',
            'Codec': 'JPEG',
            'File Type': 'jpg',
            'Registration Date': '2025-01-15 12:05:00 +0000',
            'TC Start': '01:00:30:00',
            'TC End': '01:00:42:18',
            'Shooting Day': '001',
            'Verified Backups': '1'
        }
    ]
    
    # Write CSV file
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"Created: {csv_path}")


def main():
    """Generate all demo assets."""
    print("SlateLink Demo Asset Generator")
    print("=" * 40)
    
    try:
        generate_demo_images()
        generate_demo_csv()
        
        print("\nDemo assets created successfully!")
        print("Location: test_data/")
        print("- IMG_0001.jpg, IMG_0002.jpg, IMG_0003.jpg")
        print("- exampleFilmMetadata.csv")
        print("\nTo test: python src/slatelink/app.py")
        
    except Exception as e:
        print(f"Error generating demo assets: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())