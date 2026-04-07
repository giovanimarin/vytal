# CI/CD — GitHub Actions

## Workflows

### `ci.yml` — roda em todo PR e push
- Testes backend (pytest, cobertura ≥ 80%)
- Lint backend (ruff)
- TypeScript check mobile (tsc --noEmit)

### `deploy.yml` — roda ao mergear
| Branch    | Ambiente    | Cloud Run Service              |
|-----------|-------------|-------------------------------|
| `staging` | staging     | `vytal-backend-staging`       |
| `main`    | production  | `vytal-backend-production`    |

## Secrets necessários no GitHub

Configurar em **Settings → Secrets and variables → Actions**:

| Secret                          | Descrição |
|---------------------------------|-----------|
| `GCP_PROJECT_ID`                | ID do projeto GCP (ex: `vytal-prod-123456`) |
| `GCP_WORKLOAD_IDENTITY_PROVIDER`| Provider do Workload Identity Federation |
| `GCP_SERVICE_ACCOUNT`           | Service account para deploy (ex: `github-actions@project.iam.gserviceaccount.com`) |

## Configurar Workload Identity Federation (sem chave JSON)

```bash
# 1. Criar service account
gcloud iam service-accounts create github-actions \
  --project=$PROJECT_ID

# 2. Dar permissões de deploy
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud iam service-accounts add-iam-policy-binding \
  github-actions@$PROJECT_ID.iam.gserviceaccount.com \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"

# 3. Criar Workload Identity Pool
gcloud iam workload-identity-pools create github \
  --location=global \
  --project=$PROJECT_ID

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --workload-identity-pool=github \
  --location=global \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --project=$PROJECT_ID

# 4. Vincular ao repositório GitHub
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/SEU_ORG/vytal"
```
