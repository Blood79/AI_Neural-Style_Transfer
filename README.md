# AI Neural Style Transfer

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.7-red)
![Flask](https://img.shields.io/badge/Flask-3.1-black)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED)
![CI](https://github.com/Blood79/AI_Neural-Style_Transfer/actions/workflows/ci.yml/badge.svg)

A portfolio-grade **neural style transfer** application built with PyTorch and VGG19. It combines a polished responsive UI, REST API, Docker packaging, automated tests, GitHub Actions CI, Jenkins, and AWS deployment notes.

## Features

- Upload and preview content and style images in the browser
- Adjustable style strength, optimization steps, and processing resolution
- PNG/JPEG output with one-click download
- Flask REST API
- VGG19 feature extraction with Gram-matrix style loss
- Lazy model loading with CPU/GPU auto-detection
- EXIF orientation correction and upload/pixel-count validation
- Docker + Docker Compose
- GitHub Actions CI
- Jenkins pipeline with Docker build
- AWS EC2 deployment documentation
- Large model files stay outside Git and are downloaded/cached by torchvision

## Architecture

~~~text
Browser / REST Client
        |
        v
   Flask API
        |
        v
Image validation + preprocessing
        |
        v
   VGG19 feature extractor
        |
        +---- content loss
        +---- Gram-matrix style loss
        +---- total variation loss
        |
        v
   Adam optimization
        |
        v
 Generated artwork
~~~

## Run locally

~~~bash
git clone https://github.com/Blood79/AI_Neural-Style_Transfer.git
cd AI_Neural-Style_Transfer

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
# source .venv/bin/activate

pip install -r requirements-cpu.txt
python app.py
~~~

Open http://localhost:5000.

The first style-transfer request downloads the VGG19 checkpoint through torchvision. Set the TORCH_HOME environment variable to control the cache location.

## Docker

~~~bash
docker compose up -d --build
~~~

Open http://localhost:5000.

## REST API

See [docs/API.md](docs/API.md).

~~~bash
curl -X POST http://localhost:5000/api/v1/style-transfer \
  -F "content=@content.jpg" \
  -F "style=@style.jpg" \
  -F "alpha=0.9" \
  -F "steps=40" \
  -F "max_side=512" \
  -F "format=png" \
  --output stylized.png
~~~

## CI/CD

GitHub Actions performs dependency installation, Python syntax checks, tests, and a Docker build on pushes and pull requests to main.

Jenkins performs the Python test stage and builds the production container image.

## AWS

See [docs/AWS_EC2.md](docs/AWS_EC2.md) for an EC2 deployment path.

## Attribution

This is an independently structured portfolio implementation inspired by neural style transfer and the public AI-NST project by Shradha Khapra:

https://github.com/shradha-khapra/ai-nst-project

The UI, REST API, containerization, CI/CD configuration, deployment documentation, and current application structure are part of this repository. Third-party assets and model weights remain subject to their respective licenses and terms.

## Portfolio-ready description

> Built and productionized a neural style transfer web application using PyTorch/VGG19 and Flask, adding image validation, configurable generation controls, REST API endpoints, Docker deployment, automated testing, GitHub Actions, and Jenkins CI/CD.
