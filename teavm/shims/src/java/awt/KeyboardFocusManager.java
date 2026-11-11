package java.awt;
import java.beans.PropertyChangeListener;
/** Minimal java.awt.KeyboardFocusManager. */
public abstract class KeyboardFocusManager implements java.awt.event.KeyEventDispatcher, java.awt.event.KeyEventPostProcessor {
    protected KeyboardFocusManager() {}
    public static KeyboardFocusManager getCurrentKeyboardFocusManager() { return null; }
    public static void setCurrentKeyboardFocusManager(KeyboardFocusManager m) {}
    public Window getActiveWindow() { return null; }
    public Window getFocusedWindow() { return null; }
    public Component getFocusOwner() { return null; }
    public Component getPermanentFocusOwner() { return null; }
    public void clearGlobalFocusOwner() {}
    public void clearFocusOwner() {}
    public void focusNextComponent(Component c) {}
    public void focusPreviousComponent(Component c) {}
    public void upFocusCycle(Component c) {}
    public void downFocusCycle() {}
    public boolean dispatchEvent(java.awt.AWTEvent e) { return false; }
    public boolean dispatchKeyEvent(java.awt.event.KeyEvent e) { return false; }
    public boolean postProcessKeyEvent(java.awt.event.KeyEvent e) { return false; }
    public void addPropertyChangeListener(PropertyChangeListener l) {}
    public void removePropertyChangeListener(PropertyChangeListener l) {}
    public void addPropertyChangeListener(String name, PropertyChangeListener l) {}
    public void removePropertyChangeListener(String name, PropertyChangeListener l) {}
    public void addKeyEventDispatcher(java.awt.event.KeyEventDispatcher d) {}
    public void removeKeyEventDispatcher(java.awt.event.KeyEventDispatcher d) {}
    public void addKeyEventPostProcessor(java.awt.event.KeyEventPostProcessor p) {}
    public void removeKeyEventPostProcessor(java.awt.event.KeyEventPostProcessor p) {}
}
