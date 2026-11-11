package java.io;
/** Minimal java.io.ObjectOutputStream (no serialization support). */
public class ObjectOutputStream extends OutputStream {
    public ObjectOutputStream(OutputStream out) {}
    public void writeObject(Object obj) throws IOException {}
    public void writeUnshared(Object obj) throws IOException {}
    public void defaultWriteObject() throws IOException {}
    public void writeFields() throws IOException {}
    public void reset() throws IOException {}
    public void useProtocolVersion(int version) throws IOException {}
    public void write(int val) throws IOException {}
    public void write(byte[] buf) throws IOException {}
    public void write(byte[] buf, int off, int len) throws IOException {}
    public void flush() throws IOException {}
    public void close() throws IOException {}
    public void writeBoolean(boolean val) throws IOException {}
    public void writeByte(int val) throws IOException {}
    public void writeShort(int val) throws IOException {}
    public void writeChar(int val) throws IOException {}
    public void writeInt(int val) throws IOException {}
    public void writeLong(long val) throws IOException {}
    public void writeFloat(float val) throws IOException {}
    public void writeDouble(double val) throws IOException {}
    public void writeBytes(String str) throws IOException {}
    public void writeChars(String str) throws IOException {}
    public void writeUTF(String str) throws IOException {}
}
