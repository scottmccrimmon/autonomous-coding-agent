**Acceptance Criteria**

The task is considered complete only when all of the following are true:

### Functional

* The project can be built successfully using Docker
* The container can run the MNIST training script end-to-end
* Model training behavior is unchanged relative to the non-Docker version

### Engineering Quality

* Dockerfiles follow common best practices:

  * clear base image selection
  * explicit dependency installation
  * sensible working directories
  * clean entrypoints or commands
* Dependencies are pinned or constrained appropriately
* The solution avoids unnecessary complexity

### Code Discipline

* Existing Python files are not modified unless strictly necessary
* Any changes to Python code are justified and documented
* No unused files or dead configuration are introduced

### Reproducibility & Usability

* A README explains:

  * how to build the Docker image
  * how to run training via Docker
  * any assumptions or limitations
* The workflow is understandable to a new engineer without prior context

### Reflection & Self-Assessment

* The agent provides a short explanation of:

  * design decisions made
  * alternatives considered
  * known limitations or trade-offs

### Termination Condition

* All acceptance criteria are satisfied
* The agent’s self-assessed confidence is “high” based on its own rubric
