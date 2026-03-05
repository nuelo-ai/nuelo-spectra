#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/brainstorm-idea-1.md"
OUT="$SCRIPT_DIR/brainstorm-idea-1.pdf"
WORK_DIR=$(mktemp -d)
IMG_DIR="$WORK_DIR/images"
mkdir -p "$IMG_DIR"

echo "Source: $SRC"
echo "Working in: $WORK_DIR"

# Step 1: Extract mermaid blocks → .mmd files, replace with image refs
cp "$SRC" "$WORK_DIR/doc.md"

node -e "
const fs = require('fs');
let md = fs.readFileSync(process.argv[1], 'utf8');
let i = 0;
md = md.replace(/\`\`\`mermaid\n([\s\S]*?)\n\`\`\`/g, (match, code) => {
  const idx = i++;
  fs.writeFileSync(process.argv[2] + '/diagram_' + idx + '.mmd', code.trim());
  return '<div class=\"diagram\"><img src=\"images/diagram_' + idx + '.svg\" /></div>';
});
fs.writeFileSync(process.argv[1], md);
console.log('Extracted ' + i + ' mermaid diagrams');
" "$WORK_DIR/doc.md" "$IMG_DIR"

# Step 2: Render each .mmd to SVG with constrained width
for mmd_file in "$IMG_DIR"/*.mmd; do
  [ -f "$mmd_file" ] || continue
  base=$(basename "$mmd_file" .mmd)
  echo "Rendering $base..."
  mmdc -i "$mmd_file" -o "$IMG_DIR/${base}.svg" -b transparent -w 800 --quiet 2>&1 || echo "Warning: $base failed"
done

# Step 2.5: Post-process SVGs to ensure they have width="100%" for scaling
for svg_file in "$IMG_DIR"/*.svg; do
  [ -f "$svg_file" ] || continue
  # Replace fixed width/height with viewBox-only scaling
  node -e "
    const fs = require('fs');
    let svg = fs.readFileSync(process.argv[1], 'utf8');
    // Ensure SVGs scale by setting width to 100% and removing fixed height
    svg = svg.replace(/<svg([^>]*)>/, (match, attrs) => {
      // Remove existing width/height if present
      attrs = attrs.replace(/\s*width=\"[^\"]*\"/g, '');
      attrs = attrs.replace(/\s*height=\"[^\"]*\"/g, '');
      // Add width=100% style
      if (attrs.includes('style=')) {
        attrs = attrs.replace(/style=\"/, 'style=\"width:100%;max-width:550px;height:auto;');
      } else {
        attrs += ' style=\"width:100%;max-width:550px;height:auto;\"';
      }
      return '<svg' + attrs + '>';
    });
    fs.writeFileSync(process.argv[1], svg);
  " "$svg_file"
done

echo "SVG files generated:"
ls -la "$IMG_DIR"/*.svg 2>/dev/null || echo "No SVGs found!"

# Step 3: Prepend inline CSS style block to the markdown
STYLE_BLOCK='<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #2E3440; }
h1 { font-size: 22px; border-bottom: 2px solid #5E81AC; padding-bottom: 8px; }
h2 { font-size: 18px; margin-top: 24px; color: #2E3440; }
h3 { font-size: 14px; margin-top: 16px; color: #4C566A; }
h4 { font-size: 12px; }
table { font-size: 11px; border-collapse: collapse; width: 100%; margin: 12px 0; }
th, td { border: 1px solid #D8DEE9; padding: 6px 8px; text-align: left; }
th { background: #ECEFF4; font-weight: 600; }
tr:nth-child(even) { background: #F8F9FB; }
blockquote { border-left: 3px solid #5E81AC; padding-left: 12px; color: #4C566A; margin: 12px 0; }
.diagram { text-align: center; margin: 16px 0; page-break-inside: avoid; }
.diagram img { max-width: 100%; width: auto; height: auto; display: inline-block; }
img { max-width: 100%; height: auto; }
hr { border: none; border-top: 1px solid #D8DEE9; margin: 20px 0; }
code { font-size: 11px; background: #ECEFF4; padding: 1px 4px; border-radius: 3px; }
</style>
'

cd "$WORK_DIR"
echo "$STYLE_BLOCK" | cat - doc.md > doc_styled.md
mv doc_styled.md doc.md

npx --yes md-to-pdf doc.md --pdf-options '{"format": "A4", "margin": {"top": "18mm", "bottom": "18mm", "left": "18mm", "right": "18mm"}, "printBackground": true}' 2>&1

# Step 4: Copy result
cp "$WORK_DIR/doc.pdf" "$OUT"
echo "PDF generated: $OUT"
ls -lh "$OUT"

# Cleanup
rm -rf "$WORK_DIR"
