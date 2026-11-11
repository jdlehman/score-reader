package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.Clipboard. */
public class Clipboard {
    protected String name;
    protected Transferable contents;
    protected ClipboardOwner owner;
    public Clipboard(String name) { this.name = name; }
    public String getName() { return name; }
    public synchronized void setContents(Transferable contents, ClipboardOwner owner) {
        this.contents = contents; this.owner = owner;
    }
    public synchronized Transferable getContents(Object requestor) { return contents; }
    public synchronized DataFlavor[] getAvailableDataFlavors() { return new DataFlavor[0]; }
    public synchronized boolean isDataFlavorAvailable(DataFlavor flavor) { return false; }
    public synchronized Object getData(DataFlavor flavor) throws UnsupportedFlavorException, java.io.IOException {
        throw new UnsupportedFlavorException(flavor);
    }
    public void addFlavorListener(java.awt.datatransfer.FlavorListener listener) {}
    public void removeFlavorListener(java.awt.datatransfer.FlavorListener listener) {}
    public FlavorListener[] getFlavorListeners() { return new FlavorListener[0]; }
}
