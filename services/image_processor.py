from PIL import Image, ImageDraw, ImageFont
import cv2
import os

TEMPLATE_PATH = "assets/fayda_id_template.jpg"
OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_image_to_png(input_path, user_id, mode):
    # Load template (fixed size 720x237)
    template = Image.open(TEMPLATE_PATH).convert("RGB")
    template = template.resize((720, 237))

    # Load user image
    img = cv2.imread(input_path)

    # Convert to grayscale if needed
    if mode.value == "bw":
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Detect face (optional but recommended)
    face = extract_face(img)

    # Convert face to PIL
    face_pil = Image.fromarray(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))

    # Resize face to fit ID layout
    face_pil = face_pil.resize((120, 150))  # adjust based on design

    # Paste face into template
    template.paste(face_pil, (40, 50))  # adjust position

    # Draw text (simulate ID data)
    draw = ImageDraw.Draw(template)

    try:
        font = ImageFont.truetype("assets/arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw.text((180, 60), f"User ID: {user_id}", fill=(0, 0, 0), font=font)
    draw.text((180, 90), "Name: Generated User", fill=(0, 0, 0), font=font)

    # Save output
    output_path = f"{OUTPUT_DIR}/id_{user_id}.png"
    template.save(output_path, "PNG")

    return output_path

def extract_face(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return img  # fallback

    x, y, w, h = faces[0]
    return img[y:y+h, x:x+w]
