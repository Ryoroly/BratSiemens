import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
import os

def draw_box_and_save():
    """
    Opens a file dialog, draws a predefined bounding box on the image,
    and saves the result as a new file.
    """
    root = tk.Tk()
    root.withdraw()

    # --- New coordinates for the 768x1024 image ---
    # Format: [x_min, y_min, x_max, y_max]
    coords = [60, 50, 270, 310]

    # Let the user select the "1_resized.jpeg" image
    image_path = filedialog.askopenfilename(
        title="Select the 768x1024 image file",
        filetypes=[("Image Files", "*.jpeg *.jpg *.png *.bmp *.gif *.webp")]
    )

    if not image_path:
        print("No image selected. Operation cancelled.")
        return

    try:
        image = Image.open(image_path)
        
        # Verify the image size (optional, but good practice)
        if image.size != (768, 1024):
            messagebox.showwarning(
                "Warning",
                f"The selected image is {image.size}, not 768x1024. The box might be inaccurate."
            )

        draw = ImageDraw.Draw(image)
        draw.rectangle(coords, outline="red", width=5)

        # Prepare the output filename
        directory, filename = os.path.split(image_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_CONFIRMED_boxed{ext}"
        output_path = os.path.join(directory, output_filename)

        image.save(output_path)

        success_message = f"Success!\n\nThe new image with the box was saved as:\n{output_path}"
        print(success_message)
        messagebox.showinfo("Operation Complete", success_message)

    except Exception as e:
        messagebox.showerror("Error", f"Could not process the image.\nError: {e}")
    
    root.destroy()

if __name__ == "__main__":
    draw_box_and_save()