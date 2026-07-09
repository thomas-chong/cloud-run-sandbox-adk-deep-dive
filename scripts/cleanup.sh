#!/usr/bin/env bash
set -euo pipefail

GCLOUD="${GCLOUD:-$(command -v gcloud || true)}"
if [[ -z "$GCLOUD" && -x /usr/local/share/google-cloud-sdk/bin/gcloud ]]; then
  GCLOUD=/usr/local/share/google-cloud-sdk/bin/gcloud
fi
if [[ -z "$GCLOUD" ]]; then
  echo "gcloud CLI not found" >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$($GCLOUD config get-value project)}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-sandbox-analyst-adk}"

"$GCLOUD" run services delete "$SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" --quiet

echo "Deleted Cloud Run service ${SERVICE}."
echo "The dedicated Artifact Registry repository and service account are retained."
echo "Delete them only if they are not shared with another deployment."
