package javax.imageio.stream;
import java.io.DataInput;
import java.io.IOException;
/** Minimal javax.imageio.stream.ImageInputStreamImpl (in-memory stub base). */
public abstract class ImageInputStreamImpl implements ImageInputStream {
    protected java.io.InputStream stream;
    protected ImageInputStreamImpl(java.io.InputStream stream) { this.stream = stream; }
    @Override public void setByteOrder(java.nio.ByteOrder byteOrder) {}
    @Override public java.nio.ByteOrder getByteOrder() { return java.nio.ByteOrder.BIG_ENDIAN; }
    @Override public long length() throws IOException { return 0; }
    @Override public void seek(long pos) throws IOException {}
    @Override public void close() throws IOException { if (stream != null) stream.close(); }
    @Override public void readFully(byte[] b) throws IOException {}
    @Override public void readFully(byte[] b, int off, int len) throws IOException {}
    @Override public int skipBytes(int n) throws IOException { return 0; }
    @Override public boolean readBoolean() throws IOException { return false; }
    @Override public byte readByte() throws IOException { return 0; }
    @Override public int readUnsignedByte() throws IOException { return 0; }
    @Override public short readShort() throws IOException { return 0; }
    @Override public int readUnsignedShort() throws IOException { return 0; }
    @Override public char readChar() throws IOException { return 0; }
    @Override public int readInt() throws IOException { return 0; }
    @Override public long readLong() throws IOException { return 0; }
    @Override public float readFloat() throws IOException { return 0; }
    @Override public double readDouble() throws IOException { return 0; }
    @Override public String readLine() throws IOException { return null; }
    @Override public String readUTF() throws IOException { return null; }
}
