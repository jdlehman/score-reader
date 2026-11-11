package javax.swing;
import java.awt.Component;
import java.awt.Graphics;
/** Minimal javax.swing.Icon (replaces the round-1 version with the full contract). */
public interface Icon {
    void paintIcon(Component c, Graphics g, int x, int y);
    int getIconWidth();
    int getIconHeight();
}
