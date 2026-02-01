from torch.utils.data import DataLoader

def get_dataloaders(train_ds, val_ds, batch_size: int):
    # Build loaders from preloaded datasets (e.g., W&B artifacts).
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False
    )

    return train_loader, val_loader

# Legacy dataloader function retained for reference; replaced by artifact-based pipeline.
# def get_dataloaders(batch_size: int = 64):
#     # Define standard MNIST preprocessing and normalization.
#     transform = transforms.Compose([
#         transforms.ToTensor(),
#         transforms.Normalize((0.1307,), (0.3081,))
#     ])
#
#     # Download and set up the train split.
#     train_dataset = datasets.MNIST(
#         root="./data",
#         train=True,
#         download=True,
#         transform=transform
#     )
#
#     # Download and set up the validation split.
#     val_dataset = datasets.MNIST(
#         root="./data",
#         train=False,
#         download=True,
#         transform=transform
#     )
#
#     # Wrap datasets in loaders for batching and shuffling.
#     train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
#     val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
#
#     return train_loader, val_loader
