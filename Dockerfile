docker run --rm \
  -v "$(pwd)/sites:/app/sites" \
  -v "$(pwd)/data:/app/data" \
  whistleblower --config /app/sites/example.json
