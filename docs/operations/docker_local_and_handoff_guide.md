# Docker Local and Employee Handoff Guide (metrics-catalog)

This guide converts the current local `python run.py` flow into a Docker workflow that still uses each user's own AWS profile on the host machine.

## 0. Current Docker Defaults

- Local image name: `metrics-catalog:local`
- Container name: `metrics-catalog`
- Container port: `5000`
- Default host port: `5050`
- Host port override pattern: `HOST_PORT=5051 docker compose up -d`

## 1. What This Docker Setup Does

- Builds a local image for the Flask app.
- Runs the app on port `5000` inside a container.
- Reuses the existing `.env` settings for Redshift Data API access.
- Mounts the host user's `~/.aws` directory into the container so `boto3` can use the same AWS profile that already works outside Docker.
- Publishes the app on host port `5050` by default to avoid the common macOS conflict on `5000`.
- Binds the published port to `127.0.0.1` so the app is only reachable from the local machine by default.
- Uses a read-only container filesystem with `/tmp` mounted as `tmpfs`.
- Drops Linux capabilities and blocks privilege escalation inside the container.
- Uses a Docker healthcheck that calls a lightweight Flask liveness endpoint instead of the Redshift-backed dependency check.

Important constraints:
- Do not bake AWS credentials into the image.
- Each employee must have Docker installed and a working AWS profile on their own computer.
- This container keeps the repo's current runtime model (`python run.py`). It is suitable for internal desktop use, not a production deployment pattern.
- The container still runs as root because mounted AWS profile files are commonly permissioned for owner-only read access. The compose hardening above reduces risk without breaking that access pattern.

## 2. Files Added for Docker

- `Dockerfile`
- `compose.yaml`
- `.dockerignore`

## 2.1 Why This Compose File Is Safer

The current `compose.yaml` improves safety in these ways:

- `pull_policy: never`: avoids accidental attempts to pull `metrics-catalog:local` from a public registry.
- `127.0.0.1:${HOST_PORT:-5050}:5000`: keeps the app local to the machine instead of exposing it to the full network.
- `read_only: true`: prevents writes to the container filesystem.
- `tmpfs: /tmp`: gives the app a temporary writable area without making the image writable.
- `cap_drop: [ALL]`: removes Linux capabilities the app does not need.
- `security_opt: no-new-privileges:true`: blocks privilege escalation.
- `init: true`: handles signal forwarding and process reaping more cleanly.
- `healthcheck`: verifies the Flask process is serving HTTP on `/health/live` without requiring AWS or Redshift to be available.

## 3. Prerequisites

Before starting, make sure the local machine has:

1. Docker Desktop or Docker Engine with `docker compose`.
2. AWS CLI configured for the profile you plan to use.
3. Access to Redshift Data API and Secrets Manager for the target environment.
4. This repository checked out locally for the first build.

## 4. First-Time Setup on Your Computer

### Step 1: Refresh and verify your AWS login

Use the same login pattern from `docs/operations/login_steps.md`.

1. Clear any exported static credentials:

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

2. Refresh your profile login if your organization uses SSO.

3. Verify the profile works:

```bash
aws sts get-caller-identity --profile uzsts
```

Expected result: a successful identity response.

### Step 2: Create your runtime env file

1. From the repo root, create `.env` from the template:

```bash
cp .env.example .env
```

2. Update `.env` with the real values you want the container to use:

- `AWS_PROFILE=uzsts`
- `AWS_DEFAULT_REGION=us-east-1`
- `CLUSTER_ID=<cluster-id>`
- `DATABASE=<db-name>`
- `SECRET_ARN=<secret-arn>`
- `FLASK_SECRET_KEY=<secret>`

Recommended local Docker values:

- `FLASK_DEBUG=false`
- `PORT=5000`

Important:
- Leave `PORT=5000` in `.env`.
- The container listens on `5000`.
- Docker publishes that container port to host port `5050` by default.

### Step 3: Build the Docker image

From the repo root:

```bash
docker compose build
```

This creates the local image `metrics-catalog:local`.

If you want to refresh the base image (`python:3.11-slim`) and rebuild from scratch:

```bash
docker compose build --pull --no-cache
```

### Step 4: Start the container

```bash
docker compose up -d --build
```

This publishes the app to `http://127.0.0.1:5050` by default.

If port `5050` is already in use on your computer:

```bash
HOST_PORT=5051 docker compose up -d
```

The container still listens on internal port `5000`; only the host-side published port changes.

If you previously had a failed start attempt, reset the stack before retrying:

```bash
docker compose down
docker compose up -d --build
```

If you changed `compose.yaml`, `Dockerfile`, or dependencies and want a clean rebuild:

```bash
docker compose down
docker image rm metrics-catalog:local
docker compose build --pull --no-cache
docker compose up -d
```

### Step 5: Verify the app in Docker

1. Check the container is running:

```bash
docker compose ps
```

Expected result: the service shows `healthy` after startup completes.

2. Check the Docker liveness endpoint:

```bash
curl http://127.0.0.1:5050/health/live
```

If you used `HOST_PORT=5051`, change the URL to `http://127.0.0.1:5051/health/live`.

3. Check the Redshift-backed dependency health endpoint:

```bash
curl http://127.0.0.1:5050/health
```

If you used `HOST_PORT=5051`, change the URL to `http://127.0.0.1:5051/health`.

4. Open the main pages in a browser:

- `http://127.0.0.1:5050/kpi-definitions/new`
- `http://127.0.0.1:5050/kpi-usage/new`

5. If the container fails to start, inspect logs:

```bash
docker compose logs -f
```

6. If you want to confirm the published port mapping:

```bash
docker compose ps
```

## 5. How AWS Auth Works in Docker

The compose file mounts:

```text
${HOME}/.aws -> /root/.aws
```

That means:

- The container uses the same AWS profile name defined in `.env`.
- If the host machine uses SSO, the SSO login must be refreshed on the host first.
- If `aws sts get-caller-identity --profile <profile>` fails on the host, the container will fail too.

## 6. Prepare a Handoff Package for Another Employee

After the app works on your computer, export the image so another employee can load it without building from source.

### Step 1: Save the image to a tar file

```bash
docker save metrics-catalog:local -o metrics-catalog.tar
```

If you rebuilt the image first, export the tar after the rebuild so the employee gets the latest image contents.

### Step 2: Share these handoff items

Provide the employee with:

1. `metrics-catalog.tar`
2. `.env.example` or a sanitized employee-specific env template
3. This guide

Do not send your personal `.env` file if it contains secrets you should not share.

## 7. Install on Another Employee's Computer

These steps assume the employee has Docker and AWS CLI configured locally.

### Step 1: Verify the employee's AWS profile works

On the employee's computer:

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
aws sts get-caller-identity --profile <their-profile>
```

If their organization uses SSO, they need to complete the normal SSO login flow first.

### Step 2: Create the employee env file

Have them create a local `.env` file from the template and set:

- `AWS_PROFILE=<their-profile>`
- `AWS_DEFAULT_REGION=<region>`
- `CLUSTER_ID=<cluster-id>`
- `DATABASE=<db-name>`
- `SECRET_ARN=<secret-arn>`
- `FLASK_SECRET_KEY=<secret>`
- `FLASK_DEBUG=false`
- `PORT=5000`

### Step 3: Load the image

From the folder containing `metrics-catalog.tar`:

```bash
docker load -i metrics-catalog.tar
```

### Step 4: Run the container

From the folder containing the employee `.env` file:

```bash
docker run -d \
  --name metrics-catalog \
  -p 127.0.0.1:5050:5000 \
  --env-file .env \
  -e PORT=5000 \
  -e AWS_SDK_LOAD_CONFIG=1 \
  -e AWS_SHARED_CREDENTIALS_FILE=/root/.aws/credentials \
  -e AWS_CONFIG_FILE=/root/.aws/config \
  -v "$HOME/.aws:/root/.aws:ro" \
  metrics-catalog:local
```

If port `5050` is busy, change the left side of `-p`, for example `-p 127.0.0.1:5051:5000`.

If an old container already exists on the employee machine, remove it before rerunning:

```bash
docker rm -f metrics-catalog
```

### Step 5: Verify the employee install

Check the app:

```bash
curl http://127.0.0.1:5050/health
```

If it responds successfully, open:

- `http://127.0.0.1:5050/kpi-definitions/new`
- `http://127.0.0.1:5050/kpi-usage/new`

## 8. Stop, Restart, and Remove

On your machine with compose:

```bash
docker compose stop
docker compose start
docker compose down
```

On an employee machine using `docker run`:

```bash
docker stop metrics-catalog
docker start metrics-catalog
docker rm -f metrics-catalog
```

## 9. Troubleshooting

- `AccessDeniedException`: the AWS profile does not have the required Data API or Secrets Manager permissions.
- `ResourceNotFoundException`: `SECRET_ARN`, `CLUSTER_ID`, `DATABASE`, or region are wrong.
- AWS profile errors inside Docker: verify the same profile works first on the host with `aws sts get-caller-identity --profile <profile>`.
- Container shows `unhealthy`: inspect `docker compose logs -f` and test `http://127.0.0.1:5050/health/live` first. If liveness is healthy but `/health` fails, the issue is AWS or Redshift rather than Flask startup.
- Port binding errors: use a different host port such as `HOST_PORT=5051 docker compose up -d` or `-p 5051:5000`.
- Unexpected Docker Hub pull attempt: this repo sets `pull_policy: never` in `compose.yaml`, so rerun with the updated compose file if you still see a pull error from an older local copy.
- Name already in use: remove the old container with `docker compose down` or `docker rm -f metrics-catalog`.
- Rebuild did not pick up changes: use `docker compose build --pull --no-cache` and then `docker compose up -d`.
- Container exits immediately: run `docker compose logs -f` or `docker logs metrics-catalog`.

## 10. Recommended Next Improvement

If this app will be handed off often, the next practical improvement is to store a versioned image in a private container registry and give employees a short `docker pull` plus `docker run` workflow instead of copying tar files manually.
