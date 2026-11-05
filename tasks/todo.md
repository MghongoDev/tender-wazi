# Tasks: platform

- [ ] Scaffold the repo files (.gitignore, .env.example, README.md)
  - Verify: files exist and .env is ignored
- [ ] Create the GitHub repo and push
  - Verify: gh repo view MghongoDev/tender-wazi
- [ ] Rename the Neon default branch to main and create dev
  - Verify: neon branch list shows main and dev
- [ ] Create the api schema and the api_reader role
  - Verify: the role can connect through the pooled string
- [ ] Create the storage credential and the tender-wazi-raw bucket
  - Verify: neon bucket list shows the bucket
- [ ] Write .env with the connection strings and storage vars
  - Verify: cut -d= -f1 .env shows the keys
- [ ] Run the full verification checklist
  - Verify: all checks pass
