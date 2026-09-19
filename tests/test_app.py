from io import BytesIO

from PIL import Image

from app import app


def _image_bytes(color):
    image = Image.new("RGB", (32, 32), color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_health():
    client = app.test_client()
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_style_transfer_requires_two_images():
    client = app.test_client()
    response = client.post("/api/v1/style-transfer")
    assert response.status_code == 400
    assert "required" in response.get_json()["error"].lower()


def test_invalid_extension_is_rejected():
    client = app.test_client()
    response = client.post(
        "/api/v1/style-transfer",
        data={
            "content": (BytesIO(b"not-an-image"), "content.exe"),
            "style": (_image_bytes("blue"), "style.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
