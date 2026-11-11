package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetEvent. */
public class DropTargetEvent extends java.util.EventObject {
    protected DropTargetContext context;
    public DropTargetEvent(DropTargetContext context) { super(context.getDropTarget()); this.context = context; }
    public DropTargetContext getDropTargetContext() { return context; }
}
