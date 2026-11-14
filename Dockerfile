# stage 1 build -> bulky images

FROM python:3.14 AS builder

# no need to download compile libs as this has them inbuilt

# Because /bin/ ends with a slash, 
# Docker treats it as a folder rather than a single file name. 
# It drops both binaries (/bin/uv and /bin/uvx) side-by-side inside that folder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


WORKDIR /event-management

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /event-management

RUN groupadd -r deploy_group && useradd -r -g deploy_group deploy_user

RUN chown -R deploy_user:deploy_group /event-management


COPY --from=builder --chown=deploy_user:deploy_group /event-management/.venv /event-management/.venv
COPY --chown=deploy_user:deploy_group . .

# Tell uv explicitly where the pre-built project environment is located
ENV UV_PROJECT_ENVIRONMENT="/event-management/.venv"
ENV PYTHONPATH="/event-management"
ENV PATH="/event-management/.venv/bin:$PATH"


USER deploy_user

# cmd will be decided during compose run phase