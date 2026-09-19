# REST API

Base URL: http://localhost:5000

## Health

GET /api/v1/health

Example response:

~~~json
{
  "status": "ok",
  "service": "ai-neural-style-transfer",
  "device": "cpu",
  "model_loaded": false
}
~~~

## Style transfer

POST /api/v1/style-transfer

Multipart form fields:

| Field | Type | Default | Notes |
|---|---|---:|---|
| content | file | — | JPG/PNG/WEBP |
| style | file | — | JPG/PNG/WEBP |
| alpha | float | 1.0 | Final blend from content to stylized output |
| steps | integer | 40 | Clamped to 10–120 |
| max_side | integer | 512 | Clamped to 256–768 |
| format | string | png | png or jpeg |

Example:

~~~bash
curl -X POST http://localhost:5000/api/v1/style-transfer \
  -F "content=@content.jpg" \
  -F "style=@style.jpg" \
  -F "alpha=0.85" \
  -F "steps=40" \
  -F "max_side=512" \
  -F "format=png" \
  --output stylized.png
~~~

The first generation downloads VGG19 weights through torchvision and may take longer than later requests.
