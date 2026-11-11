package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.DataFlavor. */
public class DataFlavor implements java.io.Externalizable, Cloneable {
    public static final DataFlavor stringFlavor;
    public static final DataFlavor imageFlavor;
    public static final DataFlavor javaFileListFlavor;
    static {
        DataFlavor sf = null, imf = null, jfl = null;
        try {
            sf = new DataFlavor("application/x-java-serialized-object; class=java.lang.String");
            imf = new DataFlavor("image/x-java-image; class=java.awt.Image");
            jfl = new DataFlavor("application/x-java-file-list; class=java.util.List");
        } catch (Exception ignored) {
        }
        stringFlavor = sf; imageFlavor = imf; javaFileListFlavor = jfl;
    }
    protected String mimeType;
    protected Class<?> representationClass;
    protected String humanPresentableName;
    public DataFlavor() {}
    public DataFlavor(String mimeType) { this.mimeType = mimeType; }
    public DataFlavor(Class<?> representationClass, String humanPresentableName) {
        this.representationClass = representationClass; this.humanPresentableName = humanPresentableName;
    }
    public DataFlavor(String mimeType, String humanPresentableName) throws ClassNotFoundException {
        this.mimeType = mimeType; this.humanPresentableName = humanPresentableName;
    }
    public DataFlavor(String mimeType, String humanPresentableName, ClassLoader classLoader) throws ClassNotFoundException {
        this.mimeType = mimeType; this.humanPresentableName = humanPresentableName;
    }
    public String getMimeType() { return mimeType; }
    public Class<?> getRepresentationClass() { return representationClass; }
    public String getHumanPresentableName() { return humanPresentableName; }
    public void setHumanPresentableName(String name) { humanPresentableName = name; }
    public boolean isMimeTypeEqual(DataFlavor that) { return mimeType != null && mimeType.equals(that.mimeType); }
    public boolean isMimeTypeEqual(String mimeType) { return this.mimeType != null && this.mimeType.equals(mimeType); }
    public boolean equals(Object o) { return o instanceof DataFlavor && ((DataFlavor) o).mimeType != null && ((DataFlavor) o).mimeType.equals(mimeType); }
    public boolean equals(DataFlavor that) { return equals((Object) that); }
    public int hashCode() { return mimeType == null ? 0 : mimeType.hashCode(); }
    public String toString() { return mimeType; }
    public void writeExternal(java.io.ObjectOutput out) throws java.io.IOException {}
    public void readExternal(java.io.ObjectInput in) throws java.io.IOException, ClassNotFoundException {}
    public Object clone() { return this; }
}
