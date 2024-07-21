import re
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import mimetypes
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from pathlib import Path
import json

with open('config.json', 'r') as f:
    config = json.load(f)

project_id = config["project_id"]
location = config["location"]
model_name_pro = config["model_name_pro"]
model_name_flash = config["model_name_flash"]
upload_dir = config["upload_dir"]

vertexai.init(project=project_id, location=location)

class ImageData:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_image_data()
        self._mime_type = self.get_mime_type()

    def load_image_data(self):
        with open(self.file_path, "rb") as image_file:
            return image_file.read()

    def get_mime_type(self):
        mime_type, _ = mimetypes.guess_type(self.file_path)
        return mime_type if mime_type else "application/octet-stream"

class ImageUploader:
    def __init__(self):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, image: UploadFile) -> str:
        file_location = self.upload_dir / image.filename
        with file_location.open("wb") as buffer:
            buffer.write(image.file.read())
        return str(file_location)

class ImageHandler:
    def __init__(self):
        self.uploader = ImageUploader()

    async def classify_image(self, image_path: str):
        image_object = ImageData(image_path)

        model = GenerativeModel(model_name=model_name_pro)

        role = "You're an expert in environmental well-being, knowledgeable about recyclable, non-recyclable, reusable, and non-reusable items, and their environmental impact."

        instruction = """Given an image, first identify the item/ items present in the image and give a small description on each item's physical appearance and the material composition.
                         Ensure the output is in plain text without any markdown or formatting."""

        output = "Item: [item]\nDescription: [description]\nMaterial: [material]"

        prompt = (
            f"role: {role}\n"
            f"Instruction: {instruction}\n"
            f"Output: {output}"
        )

        image_part = Part.from_image(image_object)

        contents = [prompt, image_part]
        # Generate content using the local image
        response = model.generate_content(contents)

        pattern = r"Item:\s*(.*?)\s*Description:\s*(.*?)\s*Material:\s*(.*?)(?:\n|$)"

        matches = re.findall(pattern, response.text, re.DOTALL)

        items = []

        for match in matches:
            item, description, material = match
            item_data = {
                "Item": item.strip(),
                "Description": description.strip(),
                "Material": material.strip()
            }
            items.append(item_data)

        items_list = "\n".join([f"Item: {item['Item']}, Description: {item['Description']}, Material: {item['Material']}" for item in items])

        model_2 = GenerativeModel(model_name=model_name_flash)

        role_2 = "You're an expert in environmental well-being, knowledgeable about recyclable, non-recyclable, reusable, and non-reusable items, their environmental impact, and innovative methods for recycling and reusing items."

        instruction_2 = f"""Classify each identified item from {items_list} into any of these categories with explanation of why they belong to it based on each material: Recyclable, Non-Recyclable, Reusable, Non-Reusable.
                           Ensure that no material is classified as both Recyclable and Non-Recyclable or both Reusable and Non-Reusable.
                           If the identified item and materials are of organic matters then it should be classified as Non - Recyclable and Reusable.
                           If same material is identified multiple times then do not give multiple times.
                           Suggest two simple, DIY recycling methods for Recyclable items and two reusing methods for Reusable items by combining the identified items and materials.
                           Ensure the output is in plain text without any markdown or formatting.
        """

        output_2 = """Material: [material]
        Category: [category]
        Explanation: [explanation]
        Environmental impact: [impact]
        Innovative methods: [methods]"""

        prompt_2 = (
            f"role: {role_2}\n"
            f"Instruction: {instruction_2}\n"
            f"Output: {output_2}"
        )

        # Send the final prompt 2 to the model
        contents_2 = [prompt_2]
        response_2 = model_2.generate_content(contents_2)

        return response.text, response_2.text

    async def upload_image(self, file: UploadFile) -> JSONResponse:
        file_path = self.uploader.save_image(file)
        response_text, classification_text = await self.classify_image(file_path)
        combined_response = f"{response_text}\n\n{classification_text}"
        return JSONResponse(content={"message": "Image has been uploaded", "file_path": file_path, "classification": combined_response})
    