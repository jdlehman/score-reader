package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JViewport. */
public class JViewport extends JComponent {
    protected Component view;
    public JViewport() {}
    public void setView(Component view) { this.view = view; }
    public Component getView() { return view; }
    public void setViewPosition(Point p) {}
    public Point getViewPosition() { return new Point(0, 0); }
    public Rectangle getViewRect() { return new Rectangle(0, 0, 0, 0); }
    public Dimension getExtentSize() { return new Dimension(0, 0); }
    public void setExtentSize(Dimension d) {}
    public void setViewSize(Dimension d) {}
    public void scrollRectToVisible(Rectangle r) {}
    public void addChangeListener(javax.swing.event.ChangeListener l) {}
    public void removeChangeListener(javax.swing.event.ChangeListener l) {}
    public void setScrollMode(int mode) {}
    public int getScrollMode() { return 0; }
}
