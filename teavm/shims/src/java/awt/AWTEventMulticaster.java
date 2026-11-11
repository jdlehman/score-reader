package java.awt;
import java.awt.event.*;
import java.util.EventListener;
/** Minimal java.awt.AWTEventMulticaster. */
public class AWTEventMulticaster implements ComponentListener, ContainerListener, FocusListener,
        KeyListener, MouseListener, MouseMotionListener, MouseWheelListener, WindowListener,
        WindowStateListener, WindowFocusListener, ActionListener, ItemListener, AdjustmentListener {
    protected final EventListener a, b;
    protected AWTEventMulticaster(EventListener a, EventListener b) { this.a = a; this.b = b; }
    protected static EventListener addInternal(EventListener a, EventListener b) { return a == null ? b : (b == null ? a : null); }
    protected static EventListener removeInternal(EventListener l, EventListener oldl) { return l == oldl ? null : l; }
    public static ComponentListener add(ComponentListener a, ComponentListener b) { return a == null ? b : b; }
    public static ComponentListener remove(ComponentListener l, ComponentListener oldl) { return l == oldl ? null : l; }
    public static ActionListener add(ActionListener a, ActionListener b) { return a == null ? b : b; }
    public static ActionListener remove(ActionListener l, ActionListener oldl) { return l == oldl ? null : l; }
    public static MouseListener add(MouseListener a, MouseListener b) { return a == null ? b : b; }
    public static MouseListener remove(MouseListener l, MouseListener oldl) { return l == oldl ? null : l; }
    public static MouseMotionListener add(MouseMotionListener a, MouseMotionListener b) { return a == null ? b : b; }
    public static MouseMotionListener remove(MouseMotionListener l, MouseMotionListener oldl) { return l == oldl ? null : l; }
    public static KeyListener add(KeyListener a, KeyListener b) { return a == null ? b : b; }
    public static KeyListener remove(KeyListener l, KeyListener oldl) { return l == oldl ? null : l; }
    public static FocusListener add(FocusListener a, FocusListener b) { return a == null ? b : b; }
    public static FocusListener remove(FocusListener l, FocusListener oldl) { return l == oldl ? null : l; }
    public static WindowListener add(WindowListener a, WindowListener b) { return a == null ? b : b; }
    public static WindowListener remove(WindowListener l, WindowListener oldl) { return l == oldl ? null : l; }
    public static ItemListener add(ItemListener a, ItemListener b) { return a == null ? b : b; }
    public static ItemListener remove(ItemListener l, ItemListener oldl) { return l == oldl ? null : l; }
    public static AdjustmentListener add(AdjustmentListener a, AdjustmentListener b) { return a == null ? b : b; }
    public static AdjustmentListener remove(AdjustmentListener l, AdjustmentListener oldl) { return l == oldl ? null : l; }
    public void componentResized(ComponentEvent e) {}
    public void componentMoved(ComponentEvent e) {}
    public void componentShown(ComponentEvent e) {}
    public void componentHidden(ComponentEvent e) {}
    public void componentAdded(ContainerEvent e) {}
    public void componentRemoved(ContainerEvent e) {}
    public void focusGained(FocusEvent e) {}
    public void focusLost(FocusEvent e) {}
    public void keyTyped(KeyEvent e) {}
    public void keyPressed(KeyEvent e) {}
    public void keyReleased(KeyEvent e) {}
    public void mouseClicked(MouseEvent e) {}
    public void mousePressed(MouseEvent e) {}
    public void mouseReleased(MouseEvent e) {}
    public void mouseEntered(MouseEvent e) {}
    public void mouseExited(MouseEvent e) {}
    public void mouseDragged(MouseEvent e) {}
    public void mouseMoved(MouseEvent e) {}
    public void mouseWheelMoved(MouseWheelEvent e) {}
    public void windowOpened(WindowEvent e) {}
    public void windowClosing(WindowEvent e) {}
    public void windowClosed(WindowEvent e) {}
    public void windowIconified(WindowEvent e) {}
    public void windowDeiconified(WindowEvent e) {}
    public void windowActivated(WindowEvent e) {}
    public void windowDeactivated(WindowEvent e) {}
    public void windowStateChanged(WindowEvent e) {}
    public void windowGainedFocus(WindowEvent e) {}
    public void windowLostFocus(WindowEvent e) {}
    public void actionPerformed(ActionEvent e) {}
    public void itemStateChanged(ItemEvent e) {}
    public void adjustmentValueChanged(AdjustmentEvent e) {}
}
