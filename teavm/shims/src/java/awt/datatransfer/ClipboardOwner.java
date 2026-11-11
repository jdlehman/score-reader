package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.ClipboardOwner. */
public interface ClipboardOwner {
    void lostOwnership(Clipboard clipboard, Transferable contents);
}
