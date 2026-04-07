# Terraform — Vytal GCP Infrastructure

## Pré-requisitos

- Terraform >= 1.7
- `gcloud` CLI autenticado (`gcloud auth application-default login`)
- GCP Project criado com billing ativo
- APIs habilitadas no projeto:
  ```bash
  gcloud services enable \
    run.googleapis.com \
    bigquery.googleapis.com \
    storage.googleapis.com \
    pubsub.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com
  ```

## Primeiro uso

```bash
# 1. Criar bucket para o Terraform state (uma vez só)
gsutil mb -l us-central1 gs://vytal-terraform-state

# 2. Copiar e preencher as variáveis
cd infrastructure/terraform/environments/gcp
cp terraform.tfvars.example terraform.tfvars
# editar terraform.tfvars com os valores reais

# 3. Inicializar
terraform init

# 4. Revisar o plano
terraform plan

# 5. Aplicar
terraform apply
```

## Secrets

Os secrets (Google OAuth, SECRET_KEY) são criados pelo Terraform como contêineres vazios.
Popule os valores manualmente após o primeiro `apply`:

```bash
echo -n "seu-client-id" | gcloud secrets versions add vytal-google-client-id-staging --data-file=-
echo -n "seu-client-secret" | gcloud secrets versions add vytal-google-client-secret-staging --data-file=-
echo -n "$(openssl rand -hex 32)" | gcloud secrets versions add vytal-secret-key-staging --data-file=-
```

## Estrutura

```
terraform/
├── environments/
│   └── gcp/
│       ├── main.tf               ← orquestra os módulos
│       ├── variables.tf
│       └── terraform.tfvars.example
└── modules/
    └── gcp/
        ├── cloud_run/            ← backend containerizado
        ├── storage/              ← buckets raw + processed
        ├── bigquery/             ← dataset + tabelas
        └── pubsub/               ← tópicos + DLQ
```
