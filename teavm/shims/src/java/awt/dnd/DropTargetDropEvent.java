package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetDropEvent. */
public class DropTargetDropEvent extends DropTargetEvent {
    public DropTargetDropEvent(DropTargetContext context, java.awt.Point location, int dropAction, int srcActions) {
        super(context);
    }
    public java.awt.Point getLocation() { return new java.awt.Point(0, 0); }
    public int getDropAction() { return 0; }
    public int getSourceActions() { return 0; }
    public boolean isLocalTransfer() { return false; }
    public java.awt.datatransfer.Transferable getTransferable() { return null; }
    public void acceptDrop(int dropAction) {}
    public void rejectDrop() {}
    public void dropComplete(boolean success) {}
}
