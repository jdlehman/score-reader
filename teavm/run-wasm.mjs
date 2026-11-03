// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Run the TeaVM WebAssembly build of Bench in Node.
import { load } from '../.work/teavm-bench/out-wasm-gc/runtime.mjs'
const teavm = await load(new URL('../.work/teavm-bench/out-wasm-gc/classes.wasm', import.meta.url).pathname)
teavm.exports.main([])
