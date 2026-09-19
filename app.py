import io
import os
import time

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge

from src.nst import StyleTransferEngine, image_to_bytes

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "40000000"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
engine = StyleTransferEngine()


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _read_image(file_storage) -> Image.Image:
    if not file_storage or not file_storage.filename:
        raise ValueError("Both content and style images are required.")
    if not _allowed(file_storage.filename):
        raise ValueError("Unsupported image type. Use JPG, PNG, or WEBP.")
    try:
        image = Image.open(file_storage.stream)
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc

    if image.width * image.height > MAX_PIXELS:
        raise ValueError("Image is too large in pixel count. Please upload a smaller image.")
    return image


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/v1/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "ai-neural-style-transfer",
        "device": engine.device_name,
        "model_loaded": engine.model_loaded,
    })


@app.post("/api/v1/style-transfer")
def style_transfer_api():
    started = time.perf_counter()
    try:
        content = _read_image(request.files.get("content"))
        style = _read_image(request.files.get("style"))

        steps = max(10, min(int(request.form.get("steps", 40)), 120))
        max_side = max(256, min(int(request.form.get("max_side", 512)), 768))
        alpha = max(0.0, min(float(request.form.get("alpha", 1.0)), 1.0))
        output_format = request.form.get("format", "png").lower()

        if output_format not in {"png", "jpeg"}:
            raise ValueError("format must be png or jpeg.")

        result = engine.transfer(
            content_image=content,
            style_image=style,
            steps=steps,
            max_side=max_side,
            alpha=alpha,
        )
        payload = image_to_bytes(result, output_format)
        elapsed = round(time.perf_counter() - started, 3)

        mimetype = "image/png" if output_format == "png" else "image/jpeg"
        return send_file(
            io.BytesIO(payload),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f"stylized.{output_format}",
            max_age=0,
        ), 200, {"X-Processing-Time": str(elapsed)}

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Style transfer failed")
        return jsonify({"error": "Processing failed.", "detail": str(exc)}), 500


@app.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    return jsonify({"error": "Upload too large. Reduce image size or MAX_UPLOAD_MB."}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
