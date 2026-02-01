import wandb
import torch
from torchvision import datasets, transforms
from pathlib import Path

def main():
    # Start a W&B run focused on dataset creation.
    wandb.init(
        project="mnist-cnn-wandb-tutorial",
        job_type="dataset_creation"
    )

    # Define a dataset artifact to snapshot MNIST.
    artifact = wandb.Artifact(
        name="mnist-dataset",
        type="dataset",
        description="MNIST dataset snapshot with standard normalization"
    )

    # Apply the same preprocessing used during training.
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    # Download and load train/test MNIST splits.
    train_ds = datasets.MNIST(
        root="data",
        train=True,
        download=True,
        transform=transform
    )

    test_ds = datasets.MNIST(
        root="data",
        train=False,
        download=True,
        transform=transform
    )

    # Persist datasets locally for artifact upload.
    Path("dataset_snapshot").mkdir(exist_ok=True)

    # Using the commented torch.save technique below to save data artifacts yields the following error:
    #     _pickle.UnpicklingError: Weights only load failed
    # ...because in PyTorch 2.6, torch.load() now defaults to weights_only=True.
    # PyTorch refuses to unpickle arbitrary Python objects by default for security reasons.
    # When we run the commented torch.save, we save a live Python object with methods,
    # internal state, and class references, which is unsafe.
    # In the new code, we save tensors (images, labels) making the artifact:
    #     framework-agnostic, safe to load, and future-proof.
    #
    # torch.save(train_ds, "dataset_snapshot/train.pt")
    # torch.save(test_ds, "dataset_snapshot/test.pt")

    train_images = torch.stack([x for x, _ in train_ds])
    train_labels = torch.tensor([y for _, y in train_ds])

    test_images = torch.stack([x for x, _ in test_ds])
    test_labels = torch.tensor([y for _, y in test_ds])

    Path("dataset_snapshot").mkdir(exist_ok=True)

    torch.save(
        {"images": train_images, "labels": train_labels},
        "dataset_snapshot/train.pt"
    )

    torch.save(
        {"images": test_images, "labels": test_labels},
        "dataset_snapshot/test.pt"
    )

    # Upload the dataset snapshot to W&B.
    artifact.add_dir("dataset_snapshot")
    wandb.log_artifact(artifact)

    # Close the W&B run.
    wandb.finish()

if __name__ == "__main__":
    main()
