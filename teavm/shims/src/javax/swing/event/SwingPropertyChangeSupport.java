package javax.swing.event;
import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;
import java.beans.PropertyChangeSupport;
/** Minimal javax.swing.event.SwingPropertyChangeSupport. */
public class SwingPropertyChangeSupport extends PropertyChangeSupport {
    protected boolean notifyOnEDT;
    public SwingPropertyChangeSupport(Object sourceBean) { super(sourceBean); }
    public SwingPropertyChangeSupport(Object sourceBean, boolean notifyOnEDT) {
        super(sourceBean); this.notifyOnEDT = notifyOnEDT;
    }
    public boolean isNotifyOnEDT() { return notifyOnEDT; }
    @Override public void firePropertyChange(String propertyName, Object oldValue, Object newValue) {}
    @Override public void firePropertyChange(String propertyName, boolean oldValue, boolean newValue) {}
    @Override public void firePropertyChange(String propertyName, int oldValue, int newValue) {}
    @Override public void firePropertyChange(PropertyChangeEvent evt) {}
    public void fireIndexedPropertyChange(String propertyName, int index, Object oldValue, Object newValue) {}
    public void fireIndexedPropertyChange(String propertyName, int index, boolean oldValue, boolean newValue) {}
    public void fireIndexedPropertyChange(String propertyName, int index, int oldValue, int newValue) {}
}
