package java.io;
/** Minimal java.io.LineNumberReader. */
public class LineNumberReader extends BufferedReader {
    public LineNumberReader(Reader in) { super(in); }
    public LineNumberReader(Reader in, int sz) { super(in, sz); }
    public int getLineNumber() { return 0; }
    public void setLineNumber(int lineNumber) {}
}
