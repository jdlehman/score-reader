package javax.swing.event;
/** Minimal javax.swing.event.UndoableEditListener. */
public interface UndoableEditListener extends java.util.EventListener {
    void undoableEditHappened(UndoableEditEvent e);
}
