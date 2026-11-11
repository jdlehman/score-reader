package javax.swing;
import java.awt.*;
import java.awt.event.*;
/** Minimal javax.swing.JPopupMenu. */
public class JPopupMenu extends JComponent {
    protected String label;
    public JPopupMenu() {}
    public JPopupMenu(String label) { this.label = label; }
    public JMenuItem add(JMenuItem menuItem) { return menuItem; }
    public JMenuItem add(String s) { return new JMenuItem(s); }
    public JMenuItem add(Action a) { return new JMenuItem(); }
    public void addSeparator() {}
    public void insert(Action a, int index) {}
    public void insert(Component component, int index) {}
    public void remove(int index) {}
    public void removeAll() {}
    public int getComponentCount() { return 0; }
    public void show(Component invoker, int x, int y) {}
    public void setLabel(String label) { this.label = label; }
    public String getLabel() { return label; }
    public void setLightWeightPopupEnabled(boolean b) {}
    public boolean isLightWeightPopupEnabled() { return false; }
    public void addPopupMenuListener(javax.swing.event.PopupMenuListener l) {}
    public void removePopupMenuListener(javax.swing.event.PopupMenuListener l) {}
    public javax.swing.event.PopupMenuListener[] getPopupMenuListeners() { return new javax.swing.event.PopupMenuListener[0]; }
    public void setInvoker(Component invoker) {}
    public Component getInvoker() { return null; }
    public void pack() {}
    public boolean isVisible() { return false; }
    public void setVisible(boolean b) {}
}
