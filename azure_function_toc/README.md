# Azure Function: Add PDF TOC

This Azure Function receives a PDF file (Base64 encoded), inserts a hyperlinked Table of Contents based on existing bookmarks, and returns the modified PDF (Base64 encoded).

## Deployment

Use VS Code or Azure Functions Core Tools to deploy this function to a Linux-based Azure Function App.

## Endpoint

POST https://<your-funcapp>.azurewebsites.net/api/add-pdf-toc?code=<function_key>

Content-Type: application/json

Request Body:
{
  "fileContent": "<BASE64_of_source_pdf>",
  "title": "Hyperlinked Table of Contents",
  "zoom": 1.0
}

Response:
{
  "status": "OK",
  "fileContent": "<BASE64_of_modified_pdf>"
}
