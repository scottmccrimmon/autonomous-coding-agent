import torch
from src.data import get_dataloaders

def test_dataloaders_return_loaders():
    # Ensure dataloader construction returns valid loader objects.
    train_loader, val_loader = get_dataloaders()
    assert train_loader is not None
    assert val_loader is not None

def test_batch_shapes():
    # Validate batch tensor types and expected MNIST shapes.
    train_loader, _ = get_dataloaders(batch_size=32)
    x, y = next(iter(train_loader))

    assert isinstance(x, torch.Tensor)
    assert isinstance(y, torch.Tensor)

    assert x.shape == (32, 1, 28, 28)
    assert y.shape == (32,)

def test_labels_in_valid_range():
    # Check labels are within the MNIST class range [0, 9].
    train_loader, _ = get_dataloaders(batch_size=64)
    _, y = next(iter(train_loader))

    assert y.min() >= 0
    assert y.max() <= 9
