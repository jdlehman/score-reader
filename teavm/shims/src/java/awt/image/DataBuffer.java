package java.awt.image;
/** Minimal java.awt.image.DataBuffer. */
public abstract class DataBuffer {
    public static final int TYPE_BYTE = 0;
    public static final int TYPE_USHORT = 1;
    public static final int TYPE_SHORT = 2;
    public static final int TYPE_INT = 3;
    public static final int TYPE_FLOAT = 4;
    public static final int TYPE_DOUBLE = 5;
    public static final int TYPE_UNDEFINED = 32;
    protected int dataType;
    protected int size;
    protected int numBanks;
    protected int offset;
    protected int[] offsets;
    protected DataBuffer(int dataType, int size) { this(dataType, size, 1); }
    protected DataBuffer(int dataType, int size, int numBanks) { this(dataType, size, numBanks, 0); }
    protected DataBuffer(int dataType, int size, int numBanks, int offset) {
        this.dataType = dataType; this.size = size; this.numBanks = numBanks; this.offset = offset;
        offsets = new int[numBanks];
        for (int i = 0; i < numBanks; i++) offsets[i] = offset;
    }
    public static int getDataTypeSize(int type) {
        return switch (type) {
            case TYPE_BYTE -> 8;
            case TYPE_USHORT, TYPE_SHORT -> 16;
            case TYPE_INT, TYPE_FLOAT -> 32;
            case TYPE_DOUBLE -> 64;
            default -> throw new IllegalArgumentException("Unknown data type " + type);
        };
    }
    public int getDataType() { return dataType; }
    public int getSize() { return size; }
    public int getNumBanks() { return numBanks; }
    public int getOffset() { return offset; }
    public int[] getOffsets() { return offsets.clone(); }
    public int getOffset(int bank) { return offsets[bank]; }
    public int getElem(int i) { return 0; }
    public void setElem(int i, int val) {}
}
