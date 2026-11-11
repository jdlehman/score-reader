package javax.swing;
/** Minimal javax.swing.JLayeredPane. */
public class JLayeredPane extends JComponent {
    public static final Integer DEFAULT_LAYER = 0;
    public static final Integer PALETTE_LAYER = 100;
    public static final Integer MODAL_LAYER = 200;
    public static final Integer POPUP_LAYER = 300;
    public static final Integer DRAG_LAYER = 400;
    public static final Integer FRAME_CONTENT_LAYER = -30000;
    public void add(java.awt.Component comp, Object constraints) {}
    public void setLayer(java.awt.Component c, int layer) {}
    public int getLayer(java.awt.Component c) { return 0; }
    public void setPosition(java.awt.Component c, int position) {}
    public int getPosition(java.awt.Component c) { return 0; }
}
