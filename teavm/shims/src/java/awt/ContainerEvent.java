package java.awt;
import java.awt.event.ComponentEvent;
/** Minimal java.awt.ContainerEvent. */
public class ContainerEvent extends ComponentEvent {
    public static final int CONTAINER_FIRST = 300;
    public static final int CONTAINER_LAST = 301;
    public static final int COMPONENT_ADDED = CONTAINER_FIRST;
    public static final int COMPONENT_REMOVED = 1 + CONTAINER_FIRST;
    protected Component child;
    public ContainerEvent(Component source, int id, Component child) { super(source, id); this.child = child; }
    public Component getChild() { return child; }
    public Container getContainer() { return (Container) getSource(); }
}
