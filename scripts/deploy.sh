#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${GCLOUD:-}" ]]; then
  :
elif command -v gcloud >/dev/null 2>&1; then
  GCLOUD="$(command -v gcloud)"
elif [[ -x /usr/local/share/google-cloud-sdk/bin/gcloud ]]; then
  GCLOUD=/usr/local/share/google-cloud-sdk/bin/gcloud
else
  echo "gcloud CLI not found" >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$($GCLOUD config get-value project)}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-sandbox-analyst-adk}"
CONCURRENCY="${CONCURRENCY:-1}"
REPOSITORY="${REPOSITORY:-sandbox-adk-demo}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-sandbox-adk-runner}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:latest"

printf 'Project: %s\nRegion:  %s\nService: %s\nIdentity: %s\n' \
  "$PROJECT_ID" "$REGION" "$SERVICE" "$SERVICE_ACCOUNT"

"$GCLOUD" services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  --project "$PROJECT_ID"

if ! "$GCLOUD" artifacts repositories describe "$REPOSITORY" \
  --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  "$GCLOUD" artifacts repositories create "$REPOSITORY" \
    --repository-format docker \
    --location "$REGION" \
    --description "Cloud Run Sandbox + ADK tutorial images" \
    --project "$PROJECT_ID"
fi

if ! "$GCLOUD" iam service-accounts describe "$SERVICE_ACCOUNT" \
  --project "$PROJECT_ID" >/dev/null 2>&1; then
  "$GCLOUD" iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name "Sandbox ADK tutorial runtime" \
    --project "$PROJECT_ID"
fi

for attempt in {1..12}; do
  if "$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:${SERVICE_ACCOUNT}" \
    --role roles/aiplatform.user \
    --condition None \
    --quiet >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == 12 ]]; then
    echo "Service-account IAM propagation did not complete in time" >&2
    exit 1
  fi
  sleep 5
done

"$GCLOUD" builds submit --tag "$IMAGE" --project "$PROJECT_ID" .

"$GCLOUD" beta run deploy "$SERVICE" \
  --project "$PROJECT_ID" \
  --image "$IMAGE" \
  --region "$REGION" \
  --execution-environment gen2 \
  --service-account "$SERVICE_ACCOUNT" \
  --cpu 2 \
  --memory 2Gi \
  --concurrency "$CONCURRENCY" \
  --min-instances 0 \
  --max-instances 3 \
  --timeout 3600 \
  --session-affinity \
  --sandbox-launcher \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=global,MODEL=gemini-3.5-flash,HOST_ONLY_CANARY=parent-only-not-a-secret" \
  --no-allow-unauthenticated \
  --quiet

"$GCLOUD" run services describe "$SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" \
  --format='value(status.url)'
