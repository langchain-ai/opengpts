set -euxo pipefail

langgraph build -t langchain/opengpts-langgraph:0.1.7 --platform linux/amd64,linux/arm64
docker push langchain/opengpts-langgraph:0.1.7
gcloud beta run deploy opengpts-demo-langgraph --image langchain/opengpts-langgraph:0.1.7 --region us-central1 --project langchain-dev --env-vars-file .env.gcp.yaml

docker build -t langchain/opengpts-backend:0.1.7 --platform linux/amd64,linux/arm64 .
docker push langchain/opengpts-backend:0.1.7
gcloud beta run deploy opengpts-demo-backend --image langchain/opengpts-backend:0.1.7 --region us-central1 --project langchain-dev --env-vars-file .env.gcp.yaml
