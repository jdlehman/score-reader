package javax.swing.event;
/** Minimal javax.swing.event.UndoableEditEvent. */
public class UndoableEditEvent extends java.util.EventObject {
    protected javax.swing.undo.UndoableEdit edit;
    public UndoableEditEvent(Object source, javax.swing.undo.UndoableEdit edit) { super(source); this.edit = edit; }
    public javax.swing.undo.UndoableEdit getEdit() { return edit; }
}
