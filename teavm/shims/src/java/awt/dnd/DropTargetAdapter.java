package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetAdapter. */
public abstract class DropTargetAdapter implements DropTargetListener {
    public void dragEnter(DropTargetDragEvent dtde) {}
    public void dragOver(DropTargetDragEvent dtde) {}
    public void dropActionChanged(DropTargetDragEvent dtde) {}
    public void dragExit(DropTargetEvent dte) {}
    public void drop(DropTargetDropEvent dtde) {}
}
