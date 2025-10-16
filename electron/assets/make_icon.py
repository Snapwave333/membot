from PIL import Image, ImageDraw, ImageFont
import os

def main():
    os.makedirs('assets', exist_ok=True)
    # Background
    im = Image.new('RGBA', (256, 256), (11, 18, 32, 255))
    d = ImageDraw.Draw(im)
    # Ring
    d.ellipse((28, 28, 228, 228), outline=(0, 245, 212, 255), width=10)
    # Text
    try:
        font = ImageFont.truetype("arial.ttf", 88)
    except Exception:
        font = ImageFont.load_default()
    d.text((92, 92), 'NM', fill=(0, 179, 240, 255), font=font)
    # Save multi-size ICO
    im.save('assets/icon.ico', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
    print('Wrote assets/icon.ico')

if __name__ == '__main__':
    main()


