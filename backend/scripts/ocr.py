from PIL import Image
import pytesseract
import os

def ocr_image(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

if __name__ == "__main__":
    input_path = "../data/ocr_images/"
    output_path = "../data/parsed_data/"
    os.makedirs(output_path, exist_ok=True)

    for file in os.listdir(input_path):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            ocr_text = ocr_image(os.path.join(input_path, file))
            with open(os.path.join(output_path, file.replace(".png", ".txt").replace(".jpg", ".txt")), "w", encoding="utf-8") as f:
                f.write(ocr_text)
