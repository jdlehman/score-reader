package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.Transferable. */
public interface Transferable {
    DataFlavor[] getTransferDataFlavors();
    boolean isDataFlavorSupported(DataFlavor flavor);
    Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, java.io.IOException;
}
