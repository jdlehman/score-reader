package javax.swing;
import java.awt.Image;
import java.awt.Point;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.Transferable;
import java.awt.event.InputEvent;
/** Minimal javax.swing.TransferHandler (referenced by ij.io.DragAndDropHandler). */
public class TransferHandler implements java.io.Serializable {
    public static final int NONE = 0;
    public static final int COPY = 1;
    public static final int MOVE = 2;
    public static final int COPY_OR_MOVE = COPY | MOVE;
    public static class TransferSupport {
        private final JComponent component;
        private final Transferable transferable;
        private boolean isDrop;
        private int dropAction = COPY;
        public TransferSupport(JComponent component, Transferable transferable) {
            this.component = component; this.transferable = transferable;
        }
        public JComponent getComponent() { return component; }
        public Transferable getTransferable() { return transferable; }
        public boolean isDrop() { return isDrop; }
        public void setDropAction(int dropAction) { this.dropAction = dropAction; }
        public int getDropAction() { return dropAction; }
        public int getUserDropAction() { return dropAction; }
        public void setShowDropLocation(boolean showDropLocation) {}
        public boolean isShowDropLocation() { return false; }
        public Object getDropLocation() { return null; }
        public java.awt.datatransfer.DataFlavor[] getDataFlavors() { return new java.awt.datatransfer.DataFlavor[0]; }
    }
    public TransferHandler() {}
    public TransferHandler(String property) {}
    public boolean canImport(TransferSupport support) { return false; }
    public boolean importData(TransferSupport support) { return false; }
    public void exportToClipboard(JComponent comp, Clipboard clip, int action) {}
    public void exportAsDrag(JComponent comp, InputEvent e, int action) {}
    public int getSourceActions(JComponent c) { return NONE; }
    public Transferable createTransferable(JComponent c) { return null; }
    public javax.swing.Icon getVisualRepresentation(Transferable t) { return null; }
    public javax.swing.Action getCutAction() { return null; }
    public javax.swing.Action getCopyAction() { return null; }
    public javax.swing.Action getPasteAction() { return null; }
    public Image getDragImage() { return null; }
    public void setDragImage(Image img) {}
    public Point getDragImageOffset() { return new Point(0, 0); }
    public void setDragImageOffset(Point p) {}
}
