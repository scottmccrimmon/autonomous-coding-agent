**System Role**
You are an autonomous coding agent executing an approved engineering plan.

**Task**
Implement the previously generated plan to Dockerize the MNIST CNN project.

<plan>
{{PLAN}}
</plan>

**Project Context & Constraints**

* You may read any files under `mnist-cnn/`.

* You may create or modify files **only** in the following locations:

  * `mnist-cnn/docker/` (new Docker artifacts)
  * `mnist-cnn/README.md` (documentation updates only)

* Docker artifacts **must** be created under `mnist-cnn/docker/`:

  * `Dockerfile`
  * `.dockerignore`

* Use the **existing** `requirements.txt`.

  * Do **not** create, regenerate, or modify `requirements.txt`.

* Do **not** modify source code under:

  * `mnist-cnn/src/`
  * `mnist-cnn/tests/`
    unless absolutely required for container compatibility.
  * If you believe a source code change is required, **stop and explain why** instead of proceeding.

* Assume:

  * CPU-only execution
  * Non-interactive, headless environment
  * This is a learning/demo project, not production

* Do **not** introduce:

  * Docker volume mounts
  * Orchestration tools (Compose, Kubernetes, etc.)
  * Performance tuning or architectural refactors

**Instructions**

1. Create the required Docker artifacts following standard Python and Docker best practices.
2. Keep the solution minimal, readable, and idiomatic.
3. Ensure the container can run the existing training workflow without changing model behavior.
4. Update `README.md` with clear, concise instructions for:

   * building the Docker image
   * running training via Docker
   * where outputs/logs will appear inside the container

**After completing the implementation**, briefly explain:

* What files were created or modified
* Key design decisions and why they were made
* Any assumptions or limitations that remain

Output Format

For each file you create or modify, use the following format exactly:

FILE: <relative/path/from/mnist-cnn>

<file contents>

Example:

FILE: docker/Dockerfile

FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "src/train.py"]

Repeat this FILE block for each file you create or modify.
Do not include any other text outside of these FILE blocks.