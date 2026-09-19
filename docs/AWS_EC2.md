# AWS EC2 Deployment

## Run the container

~~~bash
git clone https://github.com/Blood79/AI_Neural-Style_Transfer.git
cd AI_Neural-Style_Transfer
docker compose up -d --build
~~~

Verify locally on the instance:

~~~bash
curl http://localhost:5000/api/v1/health
~~~

For public exposure, place Nginx or an AWS Application Load Balancer in front of the application, terminate TLS at the edge, and restrict direct access to the container port.

## Notes

- The Compose volume persists the torchvision model cache.
- Neural style transfer is compute-heavy; a GPU-backed instance is more suitable for sustained inference.
- Keep the model download/cache on persistent storage so container restarts do not repeat the first-download step.
