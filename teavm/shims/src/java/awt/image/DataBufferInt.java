package java.awt.image;
/** Minimal java.awt.image.DataBufferInt. */
public final class DataBufferInt extends DataBuffer {
    int[][] bankdata;
    int[] data;
    public DataBufferInt(int size) {
        super(TYPE_INT, size);
        data = new int[size];
        bankdata = new int[][]{data};
    }
    public DataBufferInt(int[] dataArray, int size) {
        super(TYPE_INT, size);
        data = dataArray;
        bankdata = new int[][]{data};
    }
    public DataBufferInt(int[] dataArray, int size, int offset) {
        super(TYPE_INT, size, 1, offset);
        data = dataArray;
        bankdata = new int[][]{data};
    }
    public DataBufferInt(int[][] dataArray, int size) {
        super(TYPE_INT, size, dataArray.length);
        bankdata = dataArray;
        data = bankdata[0];
    }
    public int[] getData() { return data; }
    public int[] getData(int bank) { return bankdata[bank]; }
    public int[][] getBankData() { return bankdata.clone(); }
    public int getElem(int i) { return data[i + offset]; }
    public int getElem(int bank, int i) { return bankdata[bank][i + offsets[bank]]; }
    public void setElem(int i, int val) { data[i + offset] = val; }
    public void setElem(int bank, int i, int val) { bankdata[bank][i + offsets[bank]] = val; }
}
