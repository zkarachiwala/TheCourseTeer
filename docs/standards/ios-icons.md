# iOS & App Icon Standards

## Rules

- **Transparency:** iOS (apple-touch-icon) does NOT support transparency. Transparent areas render as solid black.
- **Background:** Always use a solid background colour (e.g. white or brand primary) and flatten the alpha channel.
- **Format:** Square PNG. 180×180px standard; 600×600px+ for high quality source. iOS applies rounded corners automatically — do not pre-round.
- **Placement:** `web/public/apple-touch-icon.png`

## Workflow

1. Confirm the desired background colour with the user before generating.
2. Produce the icon with a solid background (no transparency).
3. Flatten the alpha channel before saving.
4. Place the output at `web/public/apple-touch-icon.png`.
5. Verify the `<link rel="apple-touch-icon">` tag in `web/src/app/layout.tsx` points to the correct path.
