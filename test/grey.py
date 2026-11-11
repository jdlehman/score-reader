# Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
# An image as the grey pixels the page hands Audiveris (app/pdf.js, imagesToPdf and greyPage):
# turned as the photo says, on white, at most 4096 pixels on its long side, and grey by the page's
# weights. For the WebAssembly reader in Node (test/corpus.mjs with ENGINE=teavm).
#   python3 -I test/grey.py <image> <radix>   writes <radix>.grey (a byte a pixel) and <radix>.json
import json
import sys

import numpy as np
from PIL import Image, ImageOps

MAX_SIDE = 4096

src, radix = sys.argv[1], sys.argv[2]
img = ImageOps.exif_transpose(Image.open(src)).convert('RGBA')
img = Image.alpha_composite(Image.new('RGBA', img.size, (255, 255, 255, 255)), img).convert('RGB')
scale = min(1, MAX_SIDE / max(img.size))
if scale < 1:  # the browser's 'high' smoothing is close to this
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
rgb = np.asarray(img, dtype=np.uint32)
grey = ((rgb[..., 0] * 77 + rgb[..., 1] * 150 + rgb[..., 2] * 29 + 128) >> 8).astype(np.uint8)
with open(radix + '.grey', 'wb') as f:
    f.write(grey.tobytes())
with open(radix + '.json', 'w') as f:
    json.dump({'width': img.width, 'height': img.height}, f)
