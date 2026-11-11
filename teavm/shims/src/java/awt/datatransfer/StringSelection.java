package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.StringSelection. */
public class StringSelection implements Transferable, ClipboardOwner {
    protected String data;
    public StringSelection(String data) { this.data = data; }
    public DataFlavor[] getTransferDataFlavors() { return new DataFlavor[]{DataFlavor.stringFlavor}; }
    public boolean isDataFlavorSupported(DataFlavor flavor) { return DataFlavor.stringFlavor.equals(flavor); }
    public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException {
        if (!isDataFlavorSupported(flavor)) throw new UnsupportedFlavorException(flavor);
        return data;
    }
    public void lostOwnership(Clipboard clipboard, Transferable contents) {}
}
