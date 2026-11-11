package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.UnsupportedFlavorException. */
public class UnsupportedFlavorException extends Exception {
    public UnsupportedFlavorException(DataFlavor flavor) { super(flavor == null ? null : flavor.toString()); }
}
