# Plan: platform

## Goal

A working environment for the project: repo, Neon branches, credentials, storage, api_reader.

## Steps

1. Scaffold the repo: .gitignore, .env.example, README.md.
2. Create the GitHub repo and push.
3. Rename the Neon default branch to main; create dev.
4. Create the api schema and the api_reader role.
5. Create the storage credential and the tender-wazi-raw bucket on main.
6. Write .env with the direct and pooled connection strings and the storage vars.
7. Verify: git status, psql select 1, bucket list, secret scan.

## Risks

- Renaming the default branch could affect the pooler or endpoints. Mitigation: verify the connection strings afterwards.
- The api_reader role needs the api schema to exist. Mitigation: create the schema first.
- Secrets in the chat or repo. Mitigation: never echo connection strings; gitignore .env, neon.txt and the guide.

## Verification

- `git status --short` clean of secrets.
- `psql "$DATABASE_URL_DIRECT" -c "select 1"` works.
- `psql "$DATABASE_URL" -c "select 1"` works.
- `neon bucket list` shows the bucket.
