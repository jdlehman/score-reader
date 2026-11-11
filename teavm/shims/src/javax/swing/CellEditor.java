package javax.swing;
/** Minimal javax.swing.CellEditor. */
public interface CellEditor {
    Object getCellEditorValue();
    boolean isCellEditable(java.util.EventObject anEvent);
    boolean shouldSelectCell(java.util.EventObject anEvent);
    boolean stopCellEditing();
    void cancelCellEditing();
    void addCellEditorListener(javax.swing.event.CellEditorListener l);
    void removeCellEditorListener(javax.swing.event.CellEditorListener l);
}
