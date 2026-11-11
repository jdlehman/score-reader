package javax.swing;
/** Minimal javax.swing.JRootPane. */
public class JRootPane extends JComponent {
    private java.awt.Container contentPane = new javax.swing.JPanel();
    private javax.swing.JLayeredPane layeredPane = new javax.swing.JLayeredPane();
    private java.awt.Component glassPane = new javax.swing.JPanel();
    public java.awt.Container getContentPane() { return contentPane; }
    public void setContentPane(java.awt.Container contentPane) { this.contentPane = contentPane; }
    public javax.swing.JLayeredPane getLayeredPane() { return layeredPane; }
    public void setLayeredPane(javax.swing.JLayeredPane layeredPane) { this.layeredPane = layeredPane; }
    public java.awt.Component getGlassPane() { return glassPane; }
    public void setGlassPane(java.awt.Component glass) { glassPane = glass; }
    public javax.swing.JMenuBar getJMenuBar() { return null; }
    public void setJMenuBar(javax.swing.JMenuBar menu) {}
    public void setWindowDecorationStyle(int windowDecorationStyle) {}
    public int getWindowDecorationStyle() { return 0; }
}
