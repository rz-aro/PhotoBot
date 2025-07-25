from flask import Flask, render_template
from flask import send_from_directory
import os
import pickle
app = Flask(__name__)

@app.route('/')
def home():
    image_folder = 'pics'
    # images = os.listdir(image_folder)
    f = open("captions.pkl", "rb")
    caption_dict = pickle.load(f)

    return render_template('index.html', images=caption_dict)

# host files in good pics directory
@app.route('/pics/<path:filename>')
def good_pics(filename):
    print(f"Serving file: {filename}")
    return send_from_directory('Downloads', filename)

if __name__ == '__main__':
    app.run(debug=True)