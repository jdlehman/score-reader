package javax.swing;
import java.beans.PropertyChangeListener;
/** Minimal javax.swing.AbstractAction. */
public abstract class AbstractAction implements Action, Cloneable, java.io.Serializable {
    private boolean enabled = true;
    private final java.util.Map<String, Object> values = new java.util.HashMap<>();
    public AbstractAction() {}
    public AbstractAction(String name) { putValue(NAME, name); }
    public AbstractAction(String name, Icon icon) { putValue(NAME, name); putValue(SMALL_ICON, icon); }
    public Object getValue(String key) { return values.get(key); }
    public void putValue(String key, Object newValue) { values.put(key, newValue); }
    public void setEnabled(boolean newValue) { enabled = newValue; }
    public boolean isEnabled() { return enabled; }
    public Object[] getKeys() { return values.keySet().toArray(); }
    public void addPropertyChangeListener(PropertyChangeListener listener) {}
    public void removePropertyChangeListener(PropertyChangeListener listener) {}
    public abstract void actionPerformed(java.awt.event.ActionEvent e);
}
