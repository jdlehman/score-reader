package java.io;
/** Minimal java.io.SequenceInputStream (reads from the first stream only). */
public class SequenceInputStream extends InputStream {
    private InputStream in;
    public SequenceInputStream(InputStream s1, InputStream s2) { in = s1; }
    public SequenceInputStream(java.util.Enumeration<? extends InputStream> e) { in = e.hasMoreElements() ? e.nextElement() : null; }
    @Override public int read() throws IOException { return (in == null) ? -1 : in.read(); }
    @Override public int read(byte[] b, int off, int len) throws IOException { return (in == null) ? -1 : in.read(b, off, len); }
    @Override public void close() throws IOException { if (in != null) in.close(); }
}
