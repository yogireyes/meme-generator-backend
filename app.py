from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv
import requests
import random
import string
import os


load_dotenv()

temp_directory = "temp"
if not os.path.exists(temp_directory):
    os.makedirs(temp_directory)

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class MemeApi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    imageUrl = db.Column(db.String(255))


@app.route('/process_image', methods=['POST'])
def process_image():
    font_poppins_regular = os.path.join("fonts", "poppins-regular.ttf")
    font_poppins_bold = os.path.join("fonts", "poppins-bold.ttf")
    font_poppins_italic = os.path.join("fonts", "poppins-italic.ttf")
    font_poppins_bold_italic = os.path.join("fonts", "poppins-bold-italic.ttf")

    try:
        data = request.json

        # Get image from the provided URL
        img_url = data['image']
        img_response = requests.get(img_url)
        img = Image.open(BytesIO(img_response.content))

        # Get text and font properties
        text = data['text']
        font_size = data['font_size']
        font_color = data['font_color']
        text_position = (int(data['text_position']['x'] * img.width), int(data['text_position']['y'] * img.height))

        # Load fonts
        font_style = ""
        if data['is_bold'] and data['is_italic']:
            font_style = font_poppins_bold_italic
        elif data['is_bold']:
            font_style = font_poppins_bold
        elif data['is_italic']:
            font_style = font_poppins_italic
        else:
            font_style = font_poppins_regular

        font = ImageFont.truetype(font_style, size=font_size)

        # Create an ImageDraw object
        draw = ImageDraw.Draw(img)

        if data['overlay_enabled']:
            overlay_intensity = data['overlay_intensity']
            # Create a dark overlay image covering the entire original image
            overlay = Image.new('RGBA', img.size, (0, 0, 0, int(255 * overlay_intensity)))
            img.paste(overlay, (0, 0), overlay)

        # Check if background is enabled
        if data['background_enabled']:
            # Get background color
            background_color = data['background_color']

            # Get bounding box for the text
            bbox = draw.textbbox((text_position[0], text_position[1]), text, font=font)

            # Adjust bounding box with padding
            padding_x = int(data['padding_x']) + 10
            padding_y = int(data['padding_y']) + 15
            bbox = (bbox[0] - padding_x, bbox[1] - padding_y, bbox[2] + padding_x, bbox[3] + padding_y)

            # Draw background rectangle
            draw.rectangle(bbox, fill=background_color)

        # Set font size and color
        draw.text((text_position[0], text_position[1]), text, font=font, fill=font_color)

        # Save the processed image
        filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        processed_image_path = os.path.join(temp_directory, f'{filename}.jpg')
        img.save(processed_image_path)

        # Get the server address
        server_address = request.host_url.rstrip('/')

        # Return the full download path
        full_download_path = f"{server_address}/cdn/{filename}.jpg"

        return jsonify({"status": "success", "img": full_download_path})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500


@app.route("/cdn/<filename>")
def serve_file(filename):
    return send_from_directory("temp", filename)


@app.route('/storeapi', methods=['POST'])
def store_api():
    try:
        data = request.json
        new_data = MemeApi(text=data['text'], imageUrl=data['image_url'])
        db.session.add(new_data)
        db.session.commit()

        new_data_dict = {
            'id': new_data.id,
            'text': new_data.text,
            'imageUrl': new_data.imageUrl
        }

        return jsonify({"status": "success", "data": new_data_dict})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_all', methods=['GET'])
def get_all_data():
    all_data = MemeApi.query.all()
    all_data_list = [{'id': item.id, 'text': item.text, 'imageUrl': item.imageUrl} for item in all_data]
    return jsonify({"status": "success", "data": all_data_list})


@app.route('/api/get/<int:data_id>', methods=['GET'])
def get_data_by_id(data_id):
    data = MemeApi.query.get(data_id)

    if data:
        data_dict = {'id': data.id, 'text': data.text, 'imageUrl': data.imageUrl}
        return jsonify({"status": "success", "data": data_dict})
    else:
        return jsonify({"status": "error", "message": "Data not found"})


@app.route('/api/delete/<int:data_id>', methods=['DELETE'])
def delete_data_by_id(data_id):
    data = MemeApi.query.get(data_id)
    if data:
        db.session.delete(data)
        db.session.commit()
        return jsonify({"status": "success", "message": "Data deleted successfully"})
    else:
        return jsonify({"status": "error", "message": "Data not found"})


if __name__ == "__main__":
    app.run(debug=True)