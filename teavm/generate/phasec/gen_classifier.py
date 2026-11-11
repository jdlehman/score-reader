#!/usr/bin/env python3
"""Phase C (§18): convert Audiveris basic-classifier.zip (JAXB XML) into
generated Java source with the weights/norms/labels as static data, in the
same style as Phase B's PreRenderedTemplates.

Input : <audiveris-repo>/app/res/basic-classifier.zip
        (model.xml: 110 -> 149 -> 149 sigmoid MLP; means.xml/stds.xml: 110 each)
Output: teavm/entry/src/teavm/PreRenderedClassifier.java
        phasec/classifier.json (metadata + SHA-256 of every array, for the
        desktop verification harness)

Precision: Python repr() of a float round-trips exactly, so the generated
doubles are bit-identical to the XML values.
Method-size rule (Phase B lesson): javac's 64 KB per-method limit — no
builder method emits more than 16 weight rows (~1 KB/row).
"""
import hashlib
import json
import pathlib
import sys
import xml.etree.ElementTree as ET
import zipfile

REPO = pathlib.Path.home() / "workspace/score-reader-spikes/repo/.work/audiveris"
ZIP = REPO / "app/res/basic-classifier.zip"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # teavm-wasm/
OUT_JAVA = ROOT / "teavm/entry/src/teavm/PreRenderedClassifier.java"
OUT_JSON = pathlib.Path(__file__).resolve().parent / "classifier.json"

ROWS_PER_METHOD = 16


def parse_vector(path):
    root = ET.parse(path).getroot()
    assert root.tag == "vector", root.tag
    vals = [float(v.text) for v in root.findall("value")]
    return vals


def parse_model(path):
    root = ET.parse(path).getroot()
    assert root.tag == "neural-network", root.tag
    a = root.attrib
    meta = {
        "input_size": int(a["input-size"]),
        "hidden_size": int(a["hidden-size"]),
        "output_size": int(a["output-size"]),
        "learning_rate": float(a["learning-rate"]),
        "momentum": float(a["momentum"]),
        "lambda": float(a["lambda"]),
        "epochs_total": int(a["epochs-total"]),
    }
    in_labels = root.find("input-labels").text.split()
    out_labels = root.find("output-labels").text.split()

    def rows(tag):
        el = root.find(tag)
        rs = []
        for row in el.findall("row"):
            rs.append([float(item.text) for item in row.findall("item")])
        return rs

    hidden = rows("hidden-weights")
    output = rows("output-weights")
    return meta, in_labels, out_labels, hidden, output


def sha(vals):
    h = hashlib.sha256()
    for v in vals:
        h.update(repr(float(v)).encode())
        h.update(b"\n")
    return h.hexdigest()


def emit_matrix(name, matrix, lines, prefix):
    """Emit one chunk class per ROWS_PER_METHOD rows (a single class file
    cannot hold all weights: each double literal costs TWO constant-pool
    slots, and 38,889 doubles would blow the 65,535-entry pool limit).
    Chunk classes are written as separate files; `lines` gets the
    aggregator method that concatenates them. Returns the chunk file names.
    """
    chunks = [matrix[i:i + ROWS_PER_METHOD]
              for i in range(0, len(matrix), ROWS_PER_METHOD)]
    files = []
    for ci, chunk in enumerate(chunks):
        cls = f"PreRenderedClassifier{prefix}{ci}"
        files.append(cls)
        cl = []
        cl.append("package teavm;")
        cl.append("")
        cl.append(f"/** Chunk {ci} of the {name} matrix (generated — see PreRenderedClassifier). */")
        cl.append(f"public class {cls}")
        cl.append("{")
        cl.append("    public static double[][] rows ()")
        cl.append("    {")
        cl.append("        return new double[][] {")
        for row in chunk:
            cl.append("        {" + ", ".join(repr(v) for v in row) + "},")
        cl.append("        };")
        cl.append("    }")
        cl.append("}")
        p = ROOT / f"teavm/entry/src/teavm/{cls}.java"
        p.write_text("\n".join(cl))
        print(f"wrote {p} ({p.stat().st_size} bytes)")
    lines.append(f"    public static double[][] {name} ()")
    lines.append("    {")
    lines.append(f"        double[][] m = new double[{len(matrix)}][];")
    lines.append("        int r = 0;")
    for cls in files:
        lines.append(f"        for (double[] row : {cls}.rows()) {{")
        lines.append("            m[r++] = row;")
        lines.append("        }")
    lines.append("        return m;")
    lines.append("    }")
    lines.append("")
    return files


def emit_vector(name, vals, lines):
    lines.append(f"    public static double[] {name} ()")
    lines.append("    {")
    lines.append("        return new double[] {"
                 + ", ".join(repr(v) for v in vals) + "};")
    lines.append("    }")
    lines.append("")


def emit_strings(name, strs, lines):
    lines.append(f"    public static String[] {name} ()")
    lines.append("    {")
    lines.append("        return new String[] {"
                 + ", ".join('"' + s + '"' for s in strs) + "};")
    lines.append("    }")
    lines.append("")


def main():
    with zipfile.ZipFile(ZIP) as z:
        tmp = pathlib.Path("/tmp/phasec-zip")
        tmp.mkdir(exist_ok=True)
        z.extractall(tmp)
    meta, in_labels, out_labels, hidden, output = parse_model(tmp / "model.xml")
    means = parse_vector(tmp / "means.xml")
    stds = parse_vector(tmp / "stds.xml")

    # Sanity checks against the model header.
    assert len(in_labels) == meta["input_size"], (len(in_labels), meta)
    assert len(out_labels) == meta["output_size"], (len(out_labels), meta)
    assert len(hidden) == meta["hidden_size"] and all(
        len(r) == meta["input_size"] + 1 for r in hidden), "hidden shape"
    assert len(output) == meta["output_size"] and all(
        len(r) == meta["hidden_size"] + 1 for r in output), "output shape"
    assert len(means) == meta["input_size"] and len(stds) == meta["input_size"]
    assert len(set(in_labels)) == len(in_labels) and len(set(out_labels)) == len(out_labels)
    assert min(stds) > 0, "zero std would divide by zero in normalize()"

    flat_hidden = [v for row in hidden for v in row]
    flat_output = [v for row in output for v in row]
    info = {
        **meta,
        "hidden_weights_sha256": sha(flat_hidden),
        "output_weights_sha256": sha(flat_output),
        "means_sha256": sha(means),
        "stds_sha256": sha(stds),
        "input_labels": in_labels,
        "output_labels": out_labels,
        "zip": str(ZIP),
    }
    OUT_JSON.write_text(json.dumps(info, indent=2))
    print(f"wrote {OUT_JSON}")

    L = []
    L.append("package teavm;")
    L.append("")
    L.append("/**")
    L.append(" * Phase C (§18): the Audiveris basic glyph classifier (110 -> 149 -> 149")
    L.append(" * sigmoid MLP) as pre-rendered static data, generated offline from")
    L.append(" * app/res/basic-classifier.zip by phasec/gen_classifier.py.")
    L.append(" * DO NOT HAND-EDIT — regenerate. The stock loader (ZipFS + JAXB) cannot")
    L.append(" * run in WASM, so BasicClassifier (patched, ROUND 13) builds its")
    L.append(" * NeuralNetwork from these arrays instead of load(). Weights live in")
    L.append(" * per-chunk classes PreRenderedClassifierH0..H9 / O0..O9: one class")
    L.append(" * file cannot hold all 38,889 doubles (each costs TWO constant-pool")
    L.append(" * slots; the 65,535-entry pool limit breaks first).")
    L.append(" *")
    L.append(f" * Model: input={meta['input_size']} hidden={meta['hidden_size']} "
             f"output={meta['output_size']} epochs-total={meta['epochs_total']}")
    L.append(f" * hidden-weights SHA-256: {info['hidden_weights_sha256']}")
    L.append(f" * output-weights SHA-256: {info['output_weights_sha256']}")
    L.append(f" * means SHA-256: {info['means_sha256']}")
    L.append(f" * stds  SHA-256: {info['stds_sha256']}")
    L.append(" */")
    L.append("public class PreRenderedClassifier")
    L.append("{")
    L.append(f"    public static final int INPUT_SIZE = {meta['input_size']};")
    L.append(f"    public static final int HIDDEN_SIZE = {meta['hidden_size']};")
    L.append(f"    public static final int OUTPUT_SIZE = {meta['output_size']};")
    L.append(f"    public static final double LEARNING_RATE = {meta['learning_rate']!r};")
    L.append(f"    public static final double MOMENTUM = {meta['momentum']!r};")
    L.append(f"    public static final double LAMBDA = {meta['lambda']!r};")
    L.append(f"    public static final int EPOCHS_TOTAL = {meta['epochs_total']};")
    L.append("")
    emit_matrix("hiddenWeights", hidden, L, "H")
    emit_matrix("outputWeights", output, L, "O")
    emit_vector("means", means, L)
    emit_vector("stds", stds, L)
    emit_strings("inputLabels", in_labels, L)
    emit_strings("outputLabels", out_labels, L)
    L.append("}")
    OUT_JAVA.write_text("\n".join(L))
    print(f"wrote {OUT_JAVA} ({OUT_JAVA.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
