from ultralytics import YOLO

# Carrega o modelo
model = YOLO("models/medium.pt").to("mps")  # ou "cuda" conforme necessário
# Avalia o modelo no conjunto de dados

# Avalia no conjunto de validação (ou test se preferir)
metrics = model.val(data="training/dataset/data.yaml", split="val")  # ou split="test" se preferir

# Mostra os resultados
print(metrics)

