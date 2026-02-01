import torch
from torch import optim, nn
from model import CNN
from data import get_dataloaders
import wandb
from pathlib import Path

def main():
    # Initialize a W&B run and config for this experiment.
    dataset_artifact_name = "mnist-dataset:latest"
    run = wandb.init(
        project="mnist-cnn-wandb-tutorial",
        config={
            "epochs": 3,
            "batch_size": 64,
            "learning_rate": 1e-3,  # will override per run
            "optimizer": "Adam",
            "architecture": "SimpleCNN",
            "dataset": "MNIST",
            "loss": "CrossEntropyLoss",
            "data_source": "wandb_artifact",
            "dataset_artifact": dataset_artifact_name,
            "dataset_version": "v1",
            "dataset_snapshot": "dataset_snapshot",
            "model_artifact_name": "simplecnn-mnist",
            "experiment": "artifact-data",
            "promotion_intent": "candidate_model"
        }
    )

    # --- Dataset artifact usage ---
    dataset_artifact = wandb.use_artifact(
        dataset_artifact_name,
        type="dataset"
    )

    dataset_dir = dataset_artifact.download()

    # Replacing this per the new (safer) method of leveraging weights-only data artifacts.
    # train_ds = torch.load(f"{dataset_dir}/train.pt")
    # val_ds = torch.load(f"{dataset_dir}/test.pt")

    train_data = torch.load(f"{dataset_dir}/train.pt")
    val_data = torch.load(f"{dataset_dir}/test.pt")

    train_ds = torch.utils.data.TensorDataset(
        train_data["images"],
        train_data["labels"]
    )

    val_ds = torch.utils.data.TensorDataset(
        val_data["images"],
        val_data["labels"]
    )

    # Use config values to build a readable run name.
    cfg = run.config
    run.name = (
        f"{cfg.architecture}-ds:mnist-{cfg.dataset_version}-"
        f"lr{cfg.learning_rate}-bs{cfg.batch_size}"
    )

    # Pick the best available device for training.
    device = (
        "mps" if torch.backends.mps.is_available()
        else "cuda" if torch.cuda.is_available()
        else "cpu"
    )
    print(f"Using device: {device}")

    # Load data and create the model.
    train_loader, val_loader = get_dataloaders(
        train_ds=train_ds,
        val_ds=val_ds,
        batch_size=run.config.batch_size
    )
    model = CNN().to(device)

    # Set up optimizer and loss.
    lr = wandb.config.learning_rate
    optimizer = optim.Adam(model.parameters(), lr=lr)

    criterion = nn.CrossEntropyLoss()

    for epoch in range(3):
        # Training loop.
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            wandb.log({"train_loss": loss.item()})
            optimizer.step()

        print(f"Epoch {epoch+1} complete")

        # Validation loop.
        model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                outputs = model(x)
                preds = outputs.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        val_accuracy = correct / total
        wandb.log({"val_accuracy": val_accuracy})

    # Ensure the output directory exists before saving the model.
    model_dir = Path("artifacts")
    model_dir.mkdir(exist_ok=True)

    # Persist trained weights for later use.
    model_path = model_dir / "model.pt"
    torch.save(model.state_dict(), model_path)

    # Create a model artifact with descriptive metadata.
    artifact = wandb.Artifact(
        name=wandb.config.model_artifact_name,
        type="model",
        description="SimpleCNN trained on MNIST from a W&B dataset artifact",
        metadata={
            "architecture": "SimpleCNN",
            "dataset": "MNIST",
            "dataset_artifact": wandb.config.dataset_artifact,
            "data_source": wandb.config.data_source,
            "learning_rate": wandb.config.learning_rate,
            "epochs": wandb.config.epochs,
            "framework": "PyTorch"
        }
    )

    # Attach the saved weights and log the artifact to W&B.
    artifact.add_file(str(model_path))
    wandb.log_artifact(artifact)

    # Close the W&B run cleanly.
    wandb.finish()


if __name__ == "__main__":
    main()
