package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetListener. */
public interface DropTargetListener extends java.util.EventListener {
    void dragEnter(DropTargetDragEvent dtde);
    void dragOver(DropTargetDragEvent dtde);
    void dropActionChanged(DropTargetDragEvent dtde);
    void dragExit(DropTargetEvent dte);
    void drop(DropTargetDropEvent dtde);
}
