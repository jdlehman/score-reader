// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// A static server with Range requests (CheerpJ reads jars in ranges). Serves the repository root.
//   node test/serve.mjs [port]   (npm run serve)
import { createReadStream, statSync } from 'node:fs'
import { createServer } from 'node:http'
import { extname, join, normalize } from 'node:path'

const root = join(import.meta.dirname, '..')
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.jar': 'application/java-archive', '.png': 'image/png', '.jpg': 'image/jpeg', '.pdf': 'application/pdf', '.json': 'application/json', '.css': 'text/css', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml', '.wasm': 'application/wasm' }
const port = Number(process.argv[2] ?? 8787)

createServer((req, res) => {
  const { pathname } = new URL(req.url, 'http://x')
  let path = normalize(join(root, decodeURIComponent(pathname)))
  if (!path.startsWith(root)) return res.writeHead(403).end()
  let size
  try {
    let st = statSync(path)
    // a folder: its index.html if it has one (CheerpJ probes for folders; those get 404)
    if (st.isDirectory() && pathname.endsWith('/')) {
      path = join(path, 'index.html')
      st = statSync(path)
    }
    if (!st.isFile()) return res.writeHead(404).end()
    size = st.size
  } catch { return res.writeHead(404).end() }
  const headers = { 'Content-Type': types[extname(path)] ?? 'application/octet-stream', 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-cache' }
  const range = /bytes=(\d*)-(\d*)/.exec(req.headers.range ?? '')
  if (range) {
    const start = range[1] ? Number(range[1]) : size - Number(range[2])
    const end = range[1] && range[2] ? Math.min(Number(range[2]), size - 1) : size - 1
    res.writeHead(206, { ...headers, 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': end - start + 1 })
    return createReadStream(path, { start, end }).pipe(res)
  }
  res.writeHead(200, { ...headers, 'Content-Length': size })
  if (req.method === 'HEAD') return res.end()
  createReadStream(path).pipe(res)
}).listen(port, '127.0.0.1', () => console.log(`http://127.0.0.1:${port}/`))
