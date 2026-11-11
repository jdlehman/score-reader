package java.awt;
/** Minimal java.awt.ContainerListener. */
public interface ContainerListener extends java.util.EventListener {
    void componentAdded(ContainerEvent e);
    void componentRemoved(ContainerEvent e);
}
