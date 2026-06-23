# Deploying Packwell to Google Cloud Run

Target: **Cloud Run** (app) + **private Cloud SQL Postgres** (via the Cloud SQL
connector) + **Secret Manager**, mapped to `packwell.lfrankreese.com`.
Cloud Build builds the image remotely from the `Dockerfile` — **no local Docker
needed**. Migrations run automatically on container start.

> You run these in your terminal. Steps marked **(interactive)** open a browser
> or prompt you. Replace `CHANGE_ME` values.

## 0. One-time prerequisites
1. Install the gcloud CLI: `brew install --cask google-cloud-sdk`
2. **(interactive)** Log in and pick/create a project:
   ```sh
   gcloud auth login
   gcloud projects create packwell-app --name="Packwell"   # or reuse one
   ```
3. **(interactive)** Link **billing** to the project (required for Cloud Run +
   Cloud SQL) — in the Console: Billing → link your account to the project.

## 1. Set shell variables (reuse for every command below)
```sh
export PROJECT_ID=packwell-app          # your project id
export REGION=us-central1               # supports Cloud Run domain mapping
export DB_INSTANCE=packwell-db
export DB_NAME=packwell
export DB_USER=packwell
export DB_PASSWORD='CHANGE_ME_strong_password'
gcloud config set project "$PROJECT_ID"
```

## 2. Enable the APIs
```sh
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  sqladmin.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```

## 3. Create the Cloud SQL Postgres instance, DB, and user
```sh
gcloud sql instances create "$DB_INSTANCE" \
  --database-version=POSTGRES_16 --tier=db-f1-micro --region="$REGION"
gcloud sql databases create "$DB_NAME" --instance="$DB_INSTANCE"
gcloud sql users create "$DB_USER" --instance="$DB_INSTANCE" --password="$DB_PASSWORD"

export ICN=$(gcloud sql instances describe "$DB_INSTANCE" --format='value(connectionName)')
echo "Cloud SQL connection name: $ICN"   # looks like PROJECT:REGION:packwell-db
```

## 4. Store secrets (Django key + full DATABASE_URL)
The DATABASE_URL uses the Cloud SQL **socket** — no public host, IAM-authenticated.
```sh
python3 -c 'import secrets; print(secrets.token_urlsafe(50))' \
  | gcloud secrets create packwell-secret-key --data-file=-

printf '%s' "postgres://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$ICN" \
  | gcloud secrets create packwell-database-url --data-file=-
```

## 5. Let Cloud Run read the secrets + reach Cloud SQL
```sh
export PNUM=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
export RUNTIME_SA="$PNUM-compute@developer.gserviceaccount.com"

for S in packwell-secret-key packwell-database-url; do
  gcloud secrets add-iam-policy-binding "$S" \
    --member="serviceAccount:$RUNTIME_SA" --role=roles/secretmanager.secretAccessor
done
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA" --role=roles/cloudsql.client
```

## 6. Deploy (Cloud Build builds the Dockerfile remotely)
The `^@^` prefix makes `@` the delimiter, so the comma-containing values are safe.
```sh
gcloud run deploy packwell \
  --source . \
  --region="$REGION" \
  --allow-unauthenticated \
  --add-cloudsql-instances="$ICN" \
  --set-secrets=SECRET_KEY=packwell-secret-key:latest,DATABASE_URL=packwell-database-url:latest \
  --set-env-vars="^@^DEBUG=False@ALLOWED_HOSTS=.run.app,packwell.lfrankreese.com@CSRF_TRUSTED_ORIGINS=https://*.run.app,https://packwell.lfrankreese.com"
```
On success gcloud prints a `https://packwell-XXXXX.run.app` URL. Open it — the
container ran migrations on boot, so the DB is ready. **Sign up** through the
site to create your account (no superuser needed to use the app).

## 7. Map the custom domain
```sh
gcloud run domain-mappings create \
  --service=packwell --domain=packwell.lfrankreese.com --region="$REGION"
```
- **(interactive, first time)** Google may ask you to **verify ownership** of
  `lfrankreese.com` — it gives you a TXT record to add in WordPress DNS, then
  re-run the command.
- The command prints a DNS record (for a subdomain, usually a **CNAME**:
  host `packwell` → `ghs.googlehosted.com.`).

**In WordPress DNS:** add that CNAME (host `packwell`, value `ghs.googlehosted.com`).
Google auto-provisions the TLS cert (can take ~15–60 min). Then visit
**https://packwell.lfrankreese.com**.

## 8. (Optional) An admin/superuser for `/admin/`
Run it against the prod DB through the Cloud SQL proxy from your machine:
```sh
# install: https://cloud.google.com/sql/docs/postgres/sql-proxy
cloud-sql-proxy "$ICN" &           # listens on 127.0.0.1:5432
DATABASE_URL="postgres://$DB_USER:$DB_PASSWORD@127.0.0.1:5432/$DB_NAME" \
  SECRET_KEY=x .venv/bin/python manage.py createsuperuser
```

## Redeploying later
Just re-run the **step 6** `gcloud run deploy` command (secrets/SQL flags can be
omitted on later deploys — they persist on the service).

## Cost note
Cloud Run scales to zero (≈ free at idle). **Cloud SQL `db-f1-micro` runs ~$8–10/mo**
even when idle. To stop charges when not demoing:
`gcloud sql instances delete "$DB_INSTANCE"` (deletes data) or stop it in the Console.
