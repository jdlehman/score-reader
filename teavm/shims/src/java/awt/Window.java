package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Window. */
public class Window extends Container {
    public Window() {}
    public Window(Frame owner) {}
    public Window(Window owner) {}
    public Window(GraphicsConfiguration gc) {}
    public void pack() {}
    public void dispose() {}
    public void toFront() {}
    public void toBack() {}
    public void setAlwaysOnTop(boolean b) {}
    public boolean isAlwaysOnTop() { return false; }
    public void setLocationRelativeTo(Component c) {}
    public Window getOwner() { return null; }
    public void addWindowListener(WindowListener l) {}
    public void removeWindowListener(WindowListener l) {}
    public WindowListener[] getWindowListeners() { return new WindowListener[0]; }
    public void addWindowStateListener(WindowStateListener l) {}
    public void removeWindowStateListener(WindowStateListener l) {}
    public void addWindowFocusListener(WindowFocusListener l) {}
    public void removeWindowFocusListener(WindowFocusListener l) {}
    public void setIconImage(Image image) {}
    public Image getIconImage() { return null; }
    public void setMinimumSize(Dimension d) {}
}
