package javax.swing;
import java.awt.*;
import javax.swing.border.Border;
/** Minimal javax.swing.JComponent. */
public class JComponent extends Container {
    protected boolean opaque;
    protected Border border;
    public void setOpaque(boolean b) { opaque = b; }
    public boolean isOpaque() { return opaque; }
    public void setBorder(Border b) { border = b; }
    public Border getBorder() { return border; }
    public void setToolTipText(String text) {}
    public String getToolTipText() { return null; }
    public InputMap getInputMap() { return null; }
    public InputMap getInputMap(int condition) { return null; }
    public ActionMap getActionMap() { return null; }
    public void setDoubleBuffered(boolean b) {}
    public boolean isDoubleBuffered() { return false; }
    public void putClientProperty(Object key, Object value) {}
    public Object getClientProperty(Object key) { return null; }
    public void setAlignmentX(float f) {}
    public float getAlignmentX() { return 0.5f; }
    public void setAlignmentY(float f) {}
    public float getAlignmentY() { return 0.5f; }
    public Container getTopLevelAncestor() { return null; }
    public void setFocusable(boolean b) {}
    public boolean isFocusable() { return true; }
    public boolean requestFocusInWindow() { return false; }
    public void setDragEnabled(boolean b) {}
    public void setTransferHandler(javax.swing.TransferHandler newHandler) {}
    public javax.swing.TransferHandler getTransferHandler() { return null; }
    public void addAncestorListener(javax.swing.event.AncestorListener l) {}
    public void removeAncestorListener(javax.swing.event.AncestorListener l) {}
    public void setRequestFocusEnabled(boolean b) {}
    public boolean isRequestFocusEnabled() { return false; }
    public void setVerifyInputWhenFocusTarget(boolean b) {}
    public boolean getVerifyInputWhenFocusTarget() { return false; }
    public void setInheritsPopupMenu(boolean b) {}
    public boolean getInheritsPopupMenu() { return false; }
    public void setComponentPopupMenu(JPopupMenu p) {}
    public JPopupMenu getComponentPopupMenu() { return null; }
}
