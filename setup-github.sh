#!/bin/bash

# After creating the GitHub repository, run these commands:

echo "Setting up remote origin..."
git remote add origin https://github.com/wblair8689/project-context-mcp.git

echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo "✅ Repository pushed to GitHub successfully!"
echo "Repository URL: https://github.com/wblair8689/project-context-mcp"
