import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps, ImageStat, ImageColor
import webbrowser

if getattr(sys, 'frozen', False):
    APP_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_COLOR_PATH = os.path.join(APP_DIR, "logo_color.png")
LOGO_WHITE_PATH = os.path.join(APP_DIR, "logo_white.png")
ICON_PATH = os.path.join(APP_DIR, "icoautoaddlogo.ico")

LOGO_SCALE_PERCENT = 50
OFFSET = 50
MAX_WIDTH = 2000
JPEG_QUALITY = 85
MIN_LOGO_SCALE = 10
SCALE_STEP = 10
VISIBILITY_THRESHOLD = 15
COLOR_SIMILARITY_THRESHOLD = 40

def get_visibility_score(bg_region, logo_region):
    bg_gray = bg_region.convert("L")
    logo_gray = logo_region.convert("L")
    contrast = abs(ImageStat.Stat(bg_gray).mean[0] - ImageStat.Stat(logo_gray).mean[0])
    texture = ImageStat.Stat(bg_gray).stddev[0]
    return contrast - texture

def color_distance(c1, c2):
    return sum(abs(a - b) for a, b in zip(c1, c2)) / 3

def is_color_similar(bg_region, target_color, threshold=COLOR_SIMILARITY_THRESHOLD):
    bg_stat = ImageStat.Stat(bg_region)
    bg_avg = tuple(int(v) for v in bg_stat.mean[:3])
    return color_distance(bg_avg, target_color) < threshold

def find_best_position(image, logo_color, logo_white):
    img_w, img_h = image.size
    scale = LOGO_SCALE_PERCENT
    logo_dominant_color = (220, 30, 20)

    while scale >= MIN_LOGO_SCALE:
        logo_w = int(img_w * scale / 100)
        logo_h = int(logo_w * logo_color.height / logo_color.width)
        best_score = -float("inf")
        best_combo = None

        for label, logo_img in [("color", logo_color), ("white", logo_white)]:
            logo_resized = logo_img.resize((logo_w, logo_h), Image.LANCZOS)
            positions = {
                "top-left": (OFFSET, OFFSET),
                "top-right": (img_w - logo_w - OFFSET, OFFSET),
                "bottom-left": (OFFSET, img_h - logo_h - OFFSET),
                "bottom-right": (img_w - logo_w - OFFSET, img_h - logo_h - OFFSET)
            }

            for pos_name, (x, y) in positions.items():
                region = image.crop((x, y, x + logo_w, y + logo_h))
                if label == "color" and is_color_similar(region, logo_dominant_color):
                    continue
                score = get_visibility_score(region, logo_resized)
                if score > best_score:
                    best_score = score
                    best_combo = (logo_resized, (x, y))

        if best_score >= VISIBILITY_THRESHOLD:
            return best_combo

        scale -= SCALE_STEP

    logo_resized = logo_white.resize((logo_w, logo_h), Image.LANCZOS)
    return logo_resized, (img_w - logo_w - OFFSET, img_h - logo_h - OFFSET)

def paste_logo(image, logo_color, logo_white):
    logo_resized, pos = find_best_position(image, logo_color, logo_white)
    image.paste(logo_resized, pos, logo_resized)
    return image

def resize_if_needed(image):
    if image.width > MAX_WIDTH:
        ratio = MAX_WIDTH / image.width
        new_size = (MAX_WIDTH, int(image.height * ratio))
        return image.resize(new_size, Image.LANCZOS)
    return image

def process_images(input_dir):
    output_dir = os.path.join(input_dir, "avec logo")
    os.makedirs(output_dir, exist_ok=True)
    logo_color = Image.open(LOGO_COLOR_PATH).convert("RGBA")
    logo_white = Image.open(LOGO_WHITE_PATH).convert("RGBA")

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            img_path = os.path.join(input_dir, filename)
            image = Image.open(img_path)
            image = ImageOps.exif_transpose(image).convert("RGBA")
            image = paste_logo(image, logo_color, logo_white)
            image = resize_if_needed(image)
            image_rgb = image.convert("RGB")
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_name}.jpg")
            image_rgb.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)

    messagebox.showinfo("✅ Terminé", f"Images compressées enregistrées dans :\n{output_dir}")

class LogoApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Auto Add Logo")
        self.master.geometry("420x260")
        self.folder = ""

        try:
            self.master.iconbitmap(ICON_PATH)
        except:
            pass

        tk.Button(master, text="📁 Choisir dossier d'images", command=self.select_folder, width=30).pack(pady=10)
        self.label_folder = tk.Label(master, text="", fg="gray")
        self.label_folder.pack()

        tk.Button(master, text="🚀 Lancer (avec compression)", command=self.run, width=30, bg="#4CAF50", fg="white").pack(pady=20)

        credit = tk.Label(master, text="Créé par Swax", fg="blue", cursor="hand2")
        credit.pack(side="bottom", pady=10)
        credit.bind("<Button-1>", lambda e: webbrowser.open("https://swax.cc"))

    def select_folder(self):
        self.folder = filedialog.askdirectory()
        self.label_folder.config(text=self.folder)

    def run(self):
        if not self.folder:
            messagebox.showerror("❌ Erreur", "Tu dois choisir un dossier d'images.")
            return
        process_images(self.folder)

if __name__ == "__main__":
    root = tk.Tk()
    app = LogoApp(root)
    root.mainloop()
