package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JScrollPane. */
public class JScrollPane extends JComponent {
    public static final int VERTICAL_SCROLLBAR_AS_NEEDED = 20;
    public static final int VERTICAL_SCROLLBAR_NEVER = 21;
    public static final int VERTICAL_SCROLLBAR_ALWAYS = 22;
    public static final int HORIZONTAL_SCROLLBAR_AS_NEEDED = 30;
    public static final int HORIZONTAL_SCROLLBAR_NEVER = 31;
    public static final int HORIZONTAL_SCROLLBAR_ALWAYS = 32;
    protected Component view;
    protected int vsbPolicy = VERTICAL_SCROLLBAR_AS_NEEDED;
    protected int hsbPolicy = HORIZONTAL_SCROLLBAR_AS_NEEDED;
    public JScrollPane() {}
    public JScrollPane(Component view) { this.view = view; }
    public JScrollPane(Component view, int vsbPolicy, int hsbPolicy) {
        this.view = view; this.vsbPolicy = vsbPolicy; this.hsbPolicy = hsbPolicy;
    }
    public JScrollPane(int vsbPolicy, int hsbPolicy) { this.vsbPolicy = vsbPolicy; this.hsbPolicy = hsbPolicy; }
    public void setViewportView(Component view) { this.view = view; }
    public Component getViewportView() { return view; }
    public JViewport getViewport() { return null; }
    public void setViewport(JViewport viewport) {}
    public JScrollBar getVerticalScrollBar() { return null; }
    public JScrollBar getHorizontalScrollBar() { return null; }
    public void setVerticalScrollBar(JScrollBar sb) {}
    public void setHorizontalScrollBar(JScrollBar sb) {}
    public int getVerticalScrollBarPolicy() { return vsbPolicy; }
    public void setVerticalScrollBarPolicy(int p) { vsbPolicy = p; }
    public int getHorizontalScrollBarPolicy() { return hsbPolicy; }
    public void setHorizontalScrollBarPolicy(int p) { hsbPolicy = p; }
    public void setColumnHeaderView(Component view) {}
    public void setRowHeaderView(Component view) {}
    public void setWheelScrollingEnabled(boolean b) {}
    public boolean isWheelScrollingEnabled() { return false; }
}
