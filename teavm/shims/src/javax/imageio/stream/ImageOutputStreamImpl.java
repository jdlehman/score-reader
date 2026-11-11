package javax.imageio.stream;
import java.io.IOException;
/** Minimal javax.imageio.stream.ImageOutputStreamImpl (in-memory stub base). */
public abstract class ImageOutputStreamImpl implements ImageOutputStream {
    protected java.io.OutputStream stream;
    protected ImageOutputStreamImpl(java.io.OutputStream stream) { this.stream = stream; }
    @Override public void write(int b) throws IOException {}
    @Override public void close() throws IOException { if (stream != null) stream.close(); }
    @Override public void write(byte[] b) throws IOException {}
    @Override public void write(byte[] b, int off, int len) throws IOException {}
    @Override public void writeBoolean(boolean v) throws IOException {}
    @Override public void writeByte(int v) throws IOException {}
    @Override public void writeShort(int v) throws IOException {}
    @Override public void writeChar(int v) throws IOException {}
    @Override public void writeInt(int v) throws IOException {}
    @Override public void writeLong(long v) throws IOException {}
    @Override public void writeFloat(float v) throws IOException {}
    @Override public void writeDouble(double v) throws IOException {}
    @Override public void writeBytes(String s) throws IOException {}
    @Override public void writeChars(String s) throws IOException {}
    @Override public void writeUTF(String s) throws IOException {}
}
