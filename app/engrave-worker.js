// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Draws scores with Verovio for the score view (see check.js), away from the page's own thread.
// Verovio (LGPL 3.0) is served unchanged as files of its own, in verovio/.
import { serveEngraving } from './score-view.js'

serveEngraving(self, async () => {
  const { default: createModule } = await import('./verovio/verovio-module.mjs')
  const { VerovioToolkit } = await import('./verovio/verovio.mjs')
  return new VerovioToolkit(await createModule())
})
