from __future__ import annotations

import io
import threading
from dataclasses import dataclass

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision.models import VGG19_Weights, vgg19
from torchvision.transforms import functional as TF


@dataclass(frozen=True)
class EngineConfig:
    style_weight: float = 1.0e6
    content_weight: float = 1.0
    tv_weight: float = 1.0e-6


class StyleTransferEngine:
    """Lazy-loaded VGG19 neural style transfer engine."""

    STYLE_LAYERS = (0, 5, 10, 19, 28)
    CONTENT_LAYER = 21

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._features = None
        self._model_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    @property
    def device_name(self) -> str:
        return str(self.device)

    @property
    def model_loaded(self) -> bool:
        return self._features is not None

    def _load_model(self) -> torch.nn.Sequential:
        if self._features is None:
            with self._model_lock:
                if self._features is None:
                    model = vgg19(weights=VGG19_Weights.DEFAULT).features
                    model = model[: max(self.STYLE_LAYERS + (self.CONTENT_LAYER,)) + 1]
                    model.eval().to(self.device)
                    for param in model.parameters():
                        param.requires_grad = False
                    self._features = model
        return self._features

    @staticmethod
    def _preprocess(image: Image.Image, max_side: int) -> torch.Tensor:
        image = image.convert("RGB")
        scale = min(1.0, max_side / max(image.size))
        if scale < 1.0:
            new_w = max(1, int(image.width * scale))
            new_h = max(1, int(image.height * scale))
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return TF.to_tensor(image).unsqueeze(0)

    @staticmethod
    def _normalize(x: torch.Tensor) -> torch.Tensor:
        mean = torch.tensor([0.485, 0.456, 0.406], device=x.device).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], device=x.device).view(1, 3, 1, 1)
        return (x - mean) / std

    @staticmethod
    def _denormalize(x: torch.Tensor) -> torch.Tensor:
        mean = torch.tensor([0.485, 0.456, 0.406], device=x.device).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], device=x.device).view(1, 3, 1, 1)
        return (x * std + mean).clamp(0, 1)

    @staticmethod
    def _gram_matrix(features: torch.Tensor) -> torch.Tensor:
        batch, channels, height, width = features.size()
        flattened = features.view(batch, channels, height * width)
        return torch.bmm(flattened, flattened.transpose(1, 2)) / (channels * height * width)

    def transfer(
        self,
        content_image: Image.Image,
        style_image: Image.Image,
        *,
        steps: int = 40,
        max_side: int = 512,
        alpha: float = 1.0,
    ) -> Image.Image:
        model = self._load_model()

        # The model is read-only, but style transfer is memory/CPU intensive.
        # Serialize jobs so a small deployment does not OOM under concurrent requests.
        with self._inference_lock:
            content_rgb = self._preprocess(content_image, max_side)
            style_rgb = self._preprocess(style_image, max_side)
            content = self._normalize(content_rgb).to(self.device)
            style = self._normalize(style_rgb).to(self.device)

            with torch.no_grad():
                content_target = self._run_to(content, model, self.CONTENT_LAYER)
                style_targets = {
                    idx: self._gram_matrix(self._run_to(style, model, idx))
                    for idx in self.STYLE_LAYERS
                }

            target = content.clone().requires_grad_(True)
            optimizer = torch.optim.Adam([target], lr=0.03)

            for _ in range(steps):
                optimizer.zero_grad(set_to_none=True)
                content_features = self._run_to(target, model, self.CONTENT_LAYER)
                content_loss = F.mse_loss(content_features, content_target)

                style_loss = torch.zeros((), device=self.device)
                for layer_idx in self.STYLE_LAYERS:
                    generated = self._run_to(target, model, layer_idx)
                    gram = self._gram_matrix(generated)
                    style_loss = style_loss + F.mse_loss(gram, style_targets[layer_idx])

                tv_loss = (
                    torch.mean(torch.abs(target[:, :, :, 1:] - target[:, :, :, :-1]))
                    + torch.mean(torch.abs(target[:, :, 1:, :] - target[:, :, :-1, :]))
                )

                loss = (
                    self.config.content_weight * content_loss
                    + self.config.style_weight * style_loss
                    + self.config.tv_weight * tv_loss
                )
                loss.backward()
                optimizer.step()

            generated = TF.to_pil_image(self._denormalize(target.detach()).squeeze(0).cpu())

            if alpha < 1.0:
                base = content_image.convert("RGB")
                generated = generated.resize(base.size, Image.Resampling.LANCZOS)
                generated = Image.blend(base, generated, alpha)

            return generated

    @staticmethod
    def _run_to(x: torch.Tensor, model: torch.nn.Sequential, layer_idx: int) -> torch.Tensor:
        for idx, layer in enumerate(model):
            x = layer(x)
            if idx == layer_idx:
                return x
        return x


def image_to_bytes(image: Image.Image, output_format: str = "png") -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG" if output_format == "png" else "JPEG", quality=95)
    return buffer.getvalue()
