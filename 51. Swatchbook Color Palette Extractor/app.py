import numpy as np
from flask import Flask, jsonify, render_template, request
from PIL import Image, UnidentifiedImageError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit


def top_colours(img: Image.Image, n: int = 10, step: int = 16, min_dist: float = 40):
    """Return the n most common colours in an image using NumPy.

    1. Shrink the image so big photos are fast to process.
    2. Flatten it into an (N, 3) array of RGB pixels (ignoring transparent ones).
    3. Group similar shades by snapping each channel into buckets of `step`.
    4. Count each bucket with np.unique and take the bucket's average colour.
    5. Merge shades that look nearly identical so the palette isn't ten greys.
    """
    img = img.copy()
    img.thumbnail((200, 200))
    rgba = np.asarray(img.convert("RGBA")).reshape(-1, 4)
    pixels = rgba[rgba[:, 3] > 128][:, :3].astype(np.int32)  # drop transparent
    if pixels.size == 0:
        return []

    buckets = pixels // step
    keys, inverse, counts = np.unique(
        buckets, axis=0, return_inverse=True, return_counts=True
    )
    inverse = inverse.reshape(-1)

    sums = np.zeros((len(keys), 3))
    np.add.at(sums, inverse, pixels)
    means = sums / counts[:, None]  # true average colour of every bucket

    chosen = []  # [rgb, count]
    for i in np.argsort(-counts):
        colour, count = means[i], int(counts[i])
        for entry in chosen:
            if np.linalg.norm(entry[0] - colour) < min_dist:
                entry[1] += count  # near-duplicate: fold into the bigger one
                break
        else:
            if len(chosen) < n:
                chosen.append([colour, count])

    chosen.sort(key=lambda e: -e[1])
    total = len(pixels)
    result = []
    for colour, count in chosen:
        r, g, b = (int(round(v)) for v in colour)
        result.append(
            {
                "hex": f"#{r:02X}{g:02X}{b:02X}",
                "rgb": [r, g, b],
                "percent": round(count / total * 100, 1),
            }
        )
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract", methods=["POST"])
def extract():
    file = request.files.get("image")
    if file is None or file.filename == "":
        return jsonify(error="Choose an image to upload."), 400
    try:
        img = Image.open(file.stream)
        img.load()
    except (UnidentifiedImageError, OSError):
        return jsonify(error="That file isn’t a readable image. Try a PNG, JPG, WebP or GIF."), 400

    colours = top_colours(img)
    if not colours:
        return jsonify(error="That image is fully transparent, so there are no colours to read."), 400
    return jsonify(colours=colours)


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="That image is over 10 MB. Try a smaller one."), 413


if __name__ == "__main__":
    app.run(debug=True)
