#!/bin/bash

# Create dist-simple directory
rm -rf dist-simple
mkdir -p dist-simple/src/styles

# Copy manifest
cp manifest-simple.json dist-simple/manifest.json

# Copy HTML files
cp popup.html dist-simple/

# Copy JavaScript files
cp popup.js dist-simple/
cp -r src dist-simple/

# Copy styles
cp src/styles/overlay.css dist-simple/src/styles/
cp src/styles/tooltip.css dist-simple/src/styles/

# Copy icons
cp icon*.png dist-simple/

# Copy data files
cp material_insights.json dist-simple/

echo "✅ Simple build complete! Load the extension from: dist-simple/"