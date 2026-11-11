package java.io;
/** Minimal java.io.ObjectInputStream (no serialization support). */
public class ObjectInputStream extends InputStream {
    public ObjectInputStream(InputStream in) {}
    public Object readObject() throws IOException, ClassNotFoundException { return null; }
    public Object readUnshared() throws IOException, ClassNotFoundException { return null; }
    public void defaultReadObject() throws IOException, ClassNotFoundException {}
    public int read() throws IOException { return -1; }
    public int read(byte[] buf, int off, int len) throws IOException { return -1; }
    public int available() throws IOException { return 0; }
    public void close() throws IOException {}
    public boolean readBoolean() throws IOException { return false; }
    public byte readByte() throws IOException { return 0; }
    public int readUnsignedByte() throws IOException { return 0; }
    public short readShort() throws IOException { return 0; }
    public int readUnsignedShort() throws IOException { return 0; }
    public char readChar() throws IOException { return 0; }
    public int readInt() throws IOException { return 0; }
    public long readLong() throws IOException { return 0L; }
    public float readFloat() throws IOException { return 0f; }
    public double readDouble() throws IOException { return 0.0; }
    public String readUTF() throws IOException { return ""; }
    public void readFully(byte[] buf) throws IOException {}
    public void readFully(byte[] buf, int off, int len) throws IOException {}
    public int skipBytes(int n) throws IOException { return 0; }
}
