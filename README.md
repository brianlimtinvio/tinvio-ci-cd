

gcloud builds submit --tag gcr.io/oracle-329410/jaastest  --project=oracle-329410


gcloud run deploy --image gcr.io/oracle-329410/jaastest --platform managed  --project=oracle-329410 --allow-unauthenticated