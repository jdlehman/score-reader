package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Container. */
public class Container extends Component {
    public Component[] getComponents() { return new Component[0]; }
    public Component add(Component c) { if (c != null) c.parent = this; return c; }
    public Component add(Component c, int index) { return add(c); }
    public void add(Component c, Object constraints) { add(c); }
    public void add(Component c, Object constraints, int index) { add(c); }
    public void remove(Component c) {}
    public void remove(int index) {}
    public void removeAll() {}
    public int getComponentCount() { return 0; }
    public Component getComponent(int i) { throw new ArrayIndexOutOfBoundsException(i); }
    public Insets getInsets() { return new Insets(0, 0, 0, 0); }
    public void setLayout(LayoutManager lm) {}
    public LayoutManager getLayout() { return null; }
    public void addContainerListener(ContainerListener l) {}
    public void removeContainerListener(ContainerListener l) {}
    public Component add(String name, Component comp) { return add(comp); }
    public void validate() {}
    public void invalidate() {}
    public void doLayout() {}
    public void setFont(Font f) { super.setFont(f); }
}
