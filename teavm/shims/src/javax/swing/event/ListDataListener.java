package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.ListDataListener. */
public interface ListDataListener extends EventListener {
    void intervalAdded(ListDataEvent e);
    void intervalRemoved(ListDataEvent e);
    void contentsChanged(ListDataEvent e);
}
