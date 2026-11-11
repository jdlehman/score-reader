package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.TableColumnModelListener. */
public interface TableColumnModelListener extends EventListener {
    void columnAdded(TableColumnModelEvent e);
    void columnRemoved(TableColumnModelEvent e);
    void columnMoved(TableColumnModelEvent e);
    void columnMarginChanged(javax.swing.event.ChangeEvent e);
    void columnSelectionChanged(ListSelectionEvent e);
}
