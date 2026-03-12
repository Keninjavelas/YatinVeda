# PWA Icons

Place your app icons here:

- **icon-192.png** — 192×192 px PNG (required for Chrome install prompt)
- **icon-512.png** — 512×512 px PNG (required for splash screen & PWA installability)

## Generating icons

If you have a source SVG or high-resolution PNG, use a tool like:

```bash
# Using ImageMagick
convert source-icon.png -resize 192x192 icon-192.png
convert source-icon.png -resize 512x512 icon-512.png

# Or use https://realfavicongenerator.net for a complete set
```

The manifest at `public/manifest.json` references these files.
