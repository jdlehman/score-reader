package java.beans;
/** Minimal java.beans.PropertyChangeListener. */
public interface PropertyChangeListener extends java.util.EventListener {
    void propertyChange(PropertyChangeEvent evt);
}
