// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Cuts a page, or a run of pages, out of a PDF with macOS's PDFKit, keeping the scan's own pixels
// (not drawn again):
//   swiftc -O cut.swift -o cut && ./cut <in.pdf> <page or first-last, from 1> <out.pdf>
//   (`swift cut.swift` can't load PDFKit)
// PDFKit stores the image again, losslessly (Flate in place of CCITT or JBIG2), and marks it
// /Interpolate, so where PDF.js scales it a few edge pixels come out one grey level apart from the
// uncut file's (Erlkönig p. 1, measured: 0.9% of pixels by 1/255; a JBIG2 page came out identical).
import PDFKit

let a = CommandLine.arguments
let range = a.count == 4 ? a[2].split(separator: "-").compactMap { Int($0) } : []
guard a.count == 4, range.count == 1 || range.count == 2,
      let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
  FileHandle.standardError.write("usage: cut <in.pdf> <page or first-last> <out.pdf>\n".data(using: .utf8)!)
  exit(2)
}
let out = PDFDocument()
for n in range[0]...(range.last!) {
  guard let p = doc.page(at: n - 1) else { exit(2) }
  out.insert(p, at: out.pageCount)
}
guard out.write(to: URL(fileURLWithPath: a[3])) else { exit(1) }
