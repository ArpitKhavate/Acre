"""Shared training loop for the two lightweight classifiers.

MobileNetV3-Small transfer-learned on an ImageFolder dataset, exported to ONNX
with a fixed 1x3xHxW input so OpenCV DNN / ONNX Runtime on the Pi can run it
without dynamic-shape surprises.

Normalization (ImageNet mean/std) is baked into the documented preprocessing so
the edge side (edge/detect.py) must apply the SAME transform. Keep these in sync.
"""
from pathlib import Path
from typing import List, Optional

# ImageNet preprocessing — the edge side must mirror these exactly.
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def train_classifier(data_dir: str, out_onnx: Path, epochs: int, imgsz: int,
                     batch: int, workers: int = 0,
                     val_dir: Optional[str] = None) -> List[str]:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, random_split
    from torchvision import datasets, transforms, models

    device = "cuda" if torch.cuda.is_available() else "cpu"

    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(imgsz, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.2),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(int(imgsz * 1.14)),
        transforms.CenterCrop(imgsz),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])

    if val_dir:
        train_ds = datasets.ImageFolder(data_dir, transform=train_tf)
        val_ds = datasets.ImageFolder(val_dir, transform=eval_tf)
        classes = train_ds.classes
        if val_ds.classes != classes:
            raise ValueError(
                f"val_dir class names {val_ds.classes} != train {classes}"
            )
    else:
        full = datasets.ImageFolder(data_dir, transform=train_tf)
        classes = full.classes
        n_val = max(1, int(0.15 * len(full)))
        n_train = len(full) - n_val
        train_ds, val_ds = random_split(full, [n_train, n_val])
        val_ds.dataset.transform = eval_tf  # type: ignore[attr-defined]

    train_dl = DataLoader(train_ds, batch_size=batch, shuffle=True, num_workers=workers)
    val_dl = DataLoader(val_ds, batch_size=batch, num_workers=workers)

    model = models.mobilenet_v3_small(weights="IMAGENET1K_V1")
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(classes))
    model = model.to(device)

    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss_fn(model(x), y).backward()
            opt.step()

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for x, y in val_dl:
                x, y = x.to(device), y.to(device)
                pred = model(x).argmax(1)
                correct += (pred == y).sum().item()
                total += y.numel()
        print(f"epoch {epoch + 1}/{epochs}  val_acc={correct / total:.3f}")

    # Export ONNX with a static input shape.
    model.eval().cpu()
    dummy = torch.randn(1, 3, imgsz, imgsz)
    torch.onnx.export(
        model, dummy, str(out_onnx),
        input_names=["input"], output_names=["logits"],
        opset_version=12, do_constant_folding=True,
    )
    return classes
