package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetDragEvent. */
public class DropTargetDragEvent extends DropTargetEvent {
    public DropTargetDragEvent(DropTargetContext context, java.awt.Point location, int dropAction, int srcActions) {
        super(context);
    }
    public java.awt.Point getLocation() { return new java.awt.Point(0, 0); }
    public int getDropAction() { return 0; }
    public int getSourceActions() { return 0; }
    public void acceptDrag(int dragOperation) {}
    public void rejectDrag() {}
}
