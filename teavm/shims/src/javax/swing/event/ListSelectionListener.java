package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.ListSelectionListener. */
public interface ListSelectionListener extends EventListener {
    void valueChanged(ListSelectionEvent e);
}
