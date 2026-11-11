package java.beans;
/** Minimal java.beans.PropertyChangeSupport. */
public class PropertyChangeSupport {
    private final Object sourceBean;
    public PropertyChangeSupport(Object sourceBean) { this.sourceBean = sourceBean; }
    public void addPropertyChangeListener(PropertyChangeListener listener) {}
    public void removePropertyChangeListener(PropertyChangeListener listener) {}
    public void addPropertyChangeListener(String propertyName, PropertyChangeListener listener) {}
    public void removePropertyChangeListener(String propertyName, PropertyChangeListener listener) {}
    public void firePropertyChange(String propertyName, Object oldValue, Object newValue) {}
    public void firePropertyChange(String propertyName, boolean oldValue, boolean newValue) {}
    public void firePropertyChange(String propertyName, int oldValue, int newValue) {}
    public void firePropertyChange(PropertyChangeEvent evt) {}
    public boolean hasListeners(String propertyName) { return false; }
}
