#!/bin/bash
# Setup script to configure Husky pre-commit and pre-push hooks
# Run this after npm install to set up git hooks

set -e

echo "🐝 Setting up Husky hooks..."

# Check if husky is installed
if ! npm ls husky > /dev/null 2>&1; then
    echo "📦 Installing Husky..."
    npm install husky --save-dev
fi

# Initialize husky
npx husky install

# Make hooks executable
chmod +x .husky/pre-commit
chmod +x .husky/pre-push

echo ""
echo "✅ Husky setup complete!"
echo ""
echo "📋 Installed hooks:"
echo "  • pre-commit: Runs linting on staged files"
echo "  • pre-push: Runs full test suite before push"
echo ""
echo "To bypass hooks (not recommended):"
echo "  git commit --no-verify"
echo "  git push --no-verify"
