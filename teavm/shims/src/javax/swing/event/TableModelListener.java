package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.TableModelListener. */
public interface TableModelListener extends EventListener {
    void tableChanged(TableModelEvent e);
}
