
## Running with Docker

You can run the MNIST CNN training workflow in a containerized environment using Docker. The following steps assume you have Docker installed.

### 1. Build the Docker Image

Navigate to the project root (`mnist-cnn/`) and run:

```sh
docker build -f docker/Dockerfile -t mnist-cnn-train .
```

### 2. Run Training in the Container

Start the training job using:

```sh
docker run --rm mnist-cnn-train
```

This will run the `src/train.py` script inside the container.

### 3. Outputs and Logs

- Model outputs (such as checkpoints or results) will be saved in the `outputs/` directory **inside the container**.
- By default, these outputs will not persist after the container exits unless you explicitly copy files out or use Docker's volume mounting features.

### Notes

- No additional setup is required for configuration files; the `config/` directory is included in the image.
- The image uses CPU-only mode (no GPU support).
- If you need persistent outputs, see Docker docs for [using volumes](https://docs.docker.com/storage/volumes/) (not covered by default for this demo).