import torch
from src.model import CNN

def test_model_instantiation():
    # Ensure the model can be constructed.
    model = CNN()
    assert model is not None

def test_forward_pass_shape():
    # Check output logits shape for a standard MNIST batch.
    model = CNN()
    x = torch.randn(8, 1, 28, 28)  # batch of 8 MNIST images

    outputs = model(x)

    assert outputs.shape == (8, 10)

def test_model_outputs_are_finite():
    # Verify the model does not produce NaNs or infs.
    model = CNN()
    x = torch.randn(4, 1, 28, 28)

    outputs = model(x)

    assert torch.isfinite(outputs).all()
