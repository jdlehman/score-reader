package javax.imageio.stream;
import java.io.DataInput;
import java.io.IOException;
/** Minimal javax.imageio.stream.ImageInputStream. */
public interface ImageInputStream extends DataInput {
    void setByteOrder(java.nio.ByteOrder byteOrder);
    java.nio.ByteOrder getByteOrder();
    long length() throws IOException;
    void seek(long pos) throws IOException;
    void close() throws IOException;
    default long readBits(int numBits) throws IOException { return 0; }
    default int read() throws IOException { return -1; }
}
