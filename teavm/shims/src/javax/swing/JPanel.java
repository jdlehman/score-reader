package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JPanel. */
public class JPanel extends JComponent {
    public JPanel() {}
    public JPanel(LayoutManager layout) { setLayout(layout); }
    public JPanel(LayoutManager layout, boolean isDoubleBuffered) { setLayout(layout); }
    public JPanel(boolean isDoubleBuffered) {}
}
