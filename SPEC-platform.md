# Spec: platform

## Objective

A new public GitHub repo, a Neon project with a production branch and a dev branch, credentials in a local .env, a private object storage bucket, and the api_reader role.

Success looks like: the repo exists, .env is ignored, `select 1` works against dev, the bucket exists, api_reader can log in, and no secret is in the repo or the chat.

Neon free plan limits: 1 GB Postgres and 5 GB object storage per project.

## Tech Stack

- GitHub, public repo under MghongoDev
- Neon Postgres, project Kenya-tender (sweet-dawn-80243405, aws-us-east-2)
- Neon Object Storage, S3-compatible, boto3
- psql for the connection check

## Commands

Create the repo:

```
cd /home/davyce/Projects/Tender-wazi
git init -b main
gh repo create MghongoDev/tender-wazi --public --source . --remote origin --push
```

Rename the default branch to main, link the project, create dev:

```
neon branch rename br-solitary-bird-ben3owbs main
neon link --project-id sweet-dawn-80243405 --branch main
neon branch create dev --project-id sweet-dawn-80243405
```

Create the api schema and the api_reader role:

```
# Neon MCP: run_sql "CREATE SCHEMA IF NOT EXISTS api"
# Neon MCP: create_postgres_role name=api_reader access=read_only database_name=neondb schemas=["api"]
# Neon MCP: run_sql "ALTER ROLE api_reader SET statement_timeout = '5s'"
```

Create the bucket on main, then pull the storage credential into .env:

```
neon bucket create tender-wazi-raw --project-id sweet-dawn-80243405 --branch main
neon env pull --project-id sweet-dawn-80243405 --branch main --file .env -s object-storage
```

Fetch the database credentials into .env (never print them). The local .env points at dev, per the guide's checkpoint. CI uses the production strings from repository secrets:

```
neon connection-string dev --project-id sweet-dawn-80243405 --role-name neondb_owner         # DATABASE_URL_DIRECT
neon connection-string dev --project-id sweet-dawn-80243405 --role-name api_reader --pooled  # DATABASE_URL
```

Verify:

```
psql "$DATABASE_URL_DIRECT" -c "select 1"
psql "$DATABASE_URL" -c "select 1"
neon bucket list --project-id sweet-dawn-80243405 --branch main
git status --short   # .env, neon.txt and the guide must not appear
```

## Project Structure

Files this module creates:

```
tender-wazi/
  .gitignore
  .env.example
  README.md          short placeholder, expanded by ops
  CAPABILITY-MAP.md  approved map
  SPEC-platform.md   this spec
  .neon              Neon context, gitignored
  .env               gitignored
```

## Code Style

The artifacts are .gitignore and .env.example. Keep them plain and commented.

.gitignore:

```
.env
.env.local
.env.*.local
data/
neon.txt
tender-wazi-implementation-guide.md
.neon
__pycache__/
*.pyc
.venv/
```

.env.example:

```
DATABASE_URL_DIRECT=
DATABASE_URL=
RAW_BUCKET=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_ENDPOINT_URL_S3=
AWS_REGION=
ALLOWED_ORIGINS=http://localhost:8080
```

## Testing Strategy

No unit tests. Verification is a checklist:

- `git status --short` shows no .env, neon.txt, or guide.
- `psql "$DATABASE_URL_DIRECT" -c "select 1"` works against dev.
- `psql "$DATABASE_URL" -c "select 1"` works as api_reader.
- `neon bucket list` shows tender-wazi-raw.
- `git log --all -p` shows no connection string or key.

## Boundaries

- Always: keep secrets in .env; check .gitignore before the first commit; use the direct string for the pipeline and the pooled string for the API.
- Ask first: creating paid resources; changing the Neon plan; adding collaborators; renaming or deleting branches.
- Never: commit .env, neon.txt, or the guide; paste connection strings into chat, issues, or logs; use the owner role for the API.

## Success Criteria

- The repo exists on GitHub under MghongoDev, public, with .gitignore, .env.example, README.md, CAPABILITY-MAP.md and SPEC-platform.md committed.
- .env holds DATABASE_URL_DIRECT (owner, direct) and DATABASE_URL (api_reader, pooled). .env, neon.txt and the guide are ignored and absent from git.
- `psql "$DATABASE_URL_DIRECT" -c "select 1"` works against dev.
- The api_reader role exists, can log in through the pooled string, and has a 5s statement timeout.
- The tender-wazi-raw bucket exists on the main branch.
- `git log --all -p` shows no connection string or key.

## Decisions

1. Branch name: the Neon default branch "production" is renamed to "main", so the Neon branch, the GitHub default branch and the guide all agree. Renaming does not change the branch endpoint id, so connection strings stay valid.
2. Storage: one private bucket, tender-wazi-raw, on the main branch. Dev and main share it. The credential is created on main and is valid on dev (a descendant). Dev test payloads share the bucket; keys are unique (timestamp plus hash), so they do not collide.
3. Render services: created in the serve module, when the API and frontend code exist.
