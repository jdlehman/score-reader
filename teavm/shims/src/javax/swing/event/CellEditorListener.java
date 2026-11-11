package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.CellEditorListener. */
public interface CellEditorListener extends EventListener {
    void editingStopped(javax.swing.event.ChangeEvent e);
    void editingCanceled(javax.swing.event.ChangeEvent e);
}
