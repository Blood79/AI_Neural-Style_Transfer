const form = document.getElementById("transferForm");
const submitBtn = document.getElementById("submitBtn");
const statusEl = document.getElementById("status");
const resultCard = document.getElementById("resultCard");
const resultImage = document.getElementById("resultImage");
const downloadBtn = document.getElementById("downloadBtn");

function bindPreview(inputId, imageId) {
  const input = document.getElementById(inputId);
  const image = document.getElementById(imageId);
  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) return;
    image.src = URL.createObjectURL(file);
    image.classList.remove("hidden");
  });
}
bindPreview("content", "contentPreview");
bindPreview("style", "stylePreview");

function bindRange(id, outputId, formatter) {
  const input = document.getElementById(id);
  const output = document.getElementById(outputId);
  const render = () => { output.value = formatter(input.value); };
  input.addEventListener("input", render);
  render();
}
bindRange("alpha", "alphaValue", v => Math.round(Number(v) * 100) + "%");
bindRange("steps", "stepsValue", v => v);
bindRange("maxSide", "sizeValue", v => v + " px");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitBtn.disabled = true;
  submitBtn.textContent = "PROCESSING…";
  statusEl.textContent = "The neural pipeline is generating your artwork.";
  resultCard.classList.add("hidden");

  try {
    const response = await fetch("/api/v1/style-transfer", {
      method: "POST",
      body: new FormData(form)
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || "Style transfer failed.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    resultImage.src = url;
    downloadBtn.href = url;
    downloadBtn.download = "neuralart-output." + document.getElementById("format").value;
    resultCard.classList.remove("hidden");
    statusEl.textContent = "Completed in " + (response.headers.get("X-Processing-Time") || "—") + " seconds.";
    resultCard.scrollIntoView({behavior:"smooth", block:"start"});
  } catch (error) {
    statusEl.textContent = error.message;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "GENERATE ARTWORK";
  }
});
