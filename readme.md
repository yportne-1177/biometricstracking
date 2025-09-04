readme_text = """# Azure Function: Add Hyperlinked TOC to PDFs

This repository contains a serverless Azure Function that inserts a hyperlinked Table of Contents (TOC) into a PDF using PyMuPDF. It integrates with Power Automate and Power Apps to provide a fully cloud-based solution for PDF enhancement.

---

## 🚀 Features

- Adds TOC pages based on existing PDF bookmarks
- Creates internal GoTo links for navigation
- Returns modified PDF as Base64
- Integrates with OneDrive, Power Automate, and Power Apps

---

## 📦 Included Files

- `function_app.py`: Azure Function (Python v2) HTTP trigger
- `requirements.txt`: Dependencies
- `host.json`: Azure Functions config
- `README.md`: Setup and usage instructions
- `deploy/function_deploy.bicep`: Bicep template
- `deploy/function_deploy_arm.json`: ARM template
- `.vscode/launch.json`: VS Code launch configuration
- `.vscode/tasks.json`: VS Code task configuration
- `flow_build_guide.txt`: Power Automate flow setup
- `power_apps_one_pager.txt`: Power Apps screen integration

---

## 🛠 Setup Instructions

### 1. Clone the Repo


