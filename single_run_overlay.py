from PIL import Image, ImageDraw, ImageFont
import os

in_path = r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\diplomacy_news_1782868271004.png"
out_path = r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\daily_post_ready.png"
headline = "US & IRAN HOLD\nTALKS IN SWITZERLAND\nOVER INTERIM DEAL"

def add_overlay():
    try:
        font_large = ImageFont.truetype(r"C:\Windows\Fonts\impact.ttf", 80)
        font_small = ImageFont.truetype(r"C:\Windows\Fonts\impact.ttf", 40)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    img = Image.open(in_path).convert("RGBA")
    
    # Resize/Crop to Instagram square 1080x1080
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim)/2
    top = (height - min_dim)/2
    img = img.crop((left, top, left+min_dim, top+min_dim))
    img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, 700, 1080, 1080], fill=(0, 0, 0, 180))
    draw.rectangle([50, 650, 400, 720], fill=(220, 20, 60, 255))
    draw.text((70, 660), "BREAKING NEWS", font=font_small, fill=(255, 255, 255, 255))
    draw.text((50, 750), headline, font=font_large, fill=(255, 255, 255, 255))
    
    final = Image.alpha_composite(img, overlay).convert("RGB")
    final.save(out_path)
    print(f"Saved {out_path}")

if __name__ == '__main__':
    add_overlay()
