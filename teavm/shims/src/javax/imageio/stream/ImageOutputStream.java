package javax.imageio.stream;
import java.io.DataOutput;
import java.io.IOException;
/** Minimal javax.imageio.stream.ImageOutputStream. */
public interface ImageOutputStream extends DataOutput {
    void write(int b) throws IOException;
    void close() throws IOException;
}
