package javax.swing.border;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.Insets;
/** Minimal javax.swing.border.EmptyBorder. */
public class EmptyBorder implements Border, java.io.Serializable {
    protected int top, left, bottom, right;
    public EmptyBorder(int top, int left, int bottom, int right) {
        this.top = top; this.left = left; this.bottom = bottom; this.right = right;
    }
    public EmptyBorder(Insets insets) { this(insets.top, insets.left, insets.bottom, insets.right); }
    public void paintBorder(Component c, Graphics g, int x, int y, int width, int height) {}
    public Insets getBorderInsets(Component c) { return getBorderInsets(); }
    public Insets getBorderInsets() { return new Insets(top, left, bottom, right); }
    public boolean isBorderOpaque() { return false; }
}
