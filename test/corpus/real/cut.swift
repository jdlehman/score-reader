// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Cuts one page out of a PDF with macOS's PDFKit, keeping the scan's own pixels (not drawn again):
//   swiftc -O cut.swift -o cut && ./cut <in.pdf> <page, from 1> <out.pdf>   (`swift cut.swift` can't load PDFKit)
// PDFKit stores the image again, losslessly (Flate in place of CCITT or JBIG2), and marks it
// /Interpolate, so where PDF.js scales it a few edge pixels come out one grey level apart from the
// uncut file's (Erlkönig p. 1, measured: 0.9% of pixels by 1/255; a JBIG2 page came out identical).
import PDFKit

let a = CommandLine.arguments
guard a.count == 4, let page = Int(a[2]), let doc = PDFDocument(url: URL(fileURLWithPath: a[1])),
      let p = doc.page(at: page - 1) else {
  FileHandle.standardError.write("usage: cut <in.pdf> <page> <out.pdf>\n".data(using: .utf8)!)
  exit(2)
}
let out = PDFDocument()
out.insert(p, at: 0)
guard out.write(to: URL(fileURLWithPath: a[3])) else { exit(1) }
