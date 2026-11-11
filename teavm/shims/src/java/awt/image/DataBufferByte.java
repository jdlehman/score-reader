package java.awt.image;
/** Minimal java.awt.image.DataBufferByte. */
public final class DataBufferByte extends DataBuffer {
    byte[][] bankdata;
    byte[] data;
    public DataBufferByte(int size) {
        super(TYPE_BYTE, size);
        data = new byte[size];
        bankdata = new byte[][]{data};
    }
    public DataBufferByte(byte[] dataArray, int size) {
        super(TYPE_BYTE, size);
        data = dataArray;
        bankdata = new byte[][]{data};
    }
    public DataBufferByte(byte[] dataArray, int size, int offset) {
        super(TYPE_BYTE, size, 1, offset);
        data = dataArray;
        bankdata = new byte[][]{data};
    }
    public DataBufferByte(byte[][] dataArray, int size) {
        super(TYPE_BYTE, size, dataArray.length);
        bankdata = dataArray;
        data = bankdata[0];
    }
    public DataBufferByte(byte[][] dataArray, int size, int[] offsets) {
        super(TYPE_BYTE, size, dataArray.length);
        bankdata = dataArray;
        data = bankdata[0];
        System.arraycopy(offsets, 0, this.offsets, 0, offsets.length);
    }
    public byte[] getData() { return data; }
    public byte[] getData(int bank) { return bankdata[bank]; }
    public byte[][] getBankData() { return bankdata.clone(); }
    public int getElem(int i) { return data[i + offset] & 0xff; }
    public int getElem(int bank, int i) { return bankdata[bank][i + offsets[bank]] & 0xff; }
    public void setElem(int i, int val) { data[i + offset] = (byte) val; }
    public void setElem(int bank, int i, int val) { bankdata[bank][i + offsets[bank]] = (byte) val; }
}
