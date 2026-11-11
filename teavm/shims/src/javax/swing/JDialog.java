package javax.swing;
/** Minimal javax.swing.JDialog. */
public class JDialog extends java.awt.Dialog {
    public static final int DISPOSE_ON_CLOSE = 2;
    public static final int DO_NOTHING_ON_CLOSE = 0;
    public static final int HIDE_ON_CLOSE = 1;
    public static final int EXIT_ON_CLOSE = 3;
    private int defaultCloseOperation = HIDE_ON_CLOSE;
    private javax.swing.JMenuBar menuBar;
    private javax.swing.JRootPane rootPane = new javax.swing.JRootPane();
    public JDialog() { super((java.awt.Frame) null); }
    public JDialog(java.awt.Frame owner) { super(owner); }
    public JDialog(java.awt.Frame owner, boolean modal) { super(owner, modal); }
    public JDialog(java.awt.Frame owner, String title) { super(owner, title); }
    public JDialog(java.awt.Frame owner, String title, boolean modal) { super(owner, title, modal); }
    public JDialog(java.awt.Dialog owner) { super(owner); }
    public JDialog(java.awt.Dialog owner, boolean modal) { super(owner); this.modal = modal; }
    public JDialog(java.awt.Dialog owner, String title) { super(owner, title); }
    public JDialog(java.awt.Dialog owner, String title, boolean modal) { super(owner, title); this.modal = modal; }
    public JDialog(java.awt.Frame owner, String title, boolean modal, java.awt.GraphicsConfiguration gc) { super(owner, title, modal); }
    public void setDefaultCloseOperation(int operation) { defaultCloseOperation = operation; }
    public int getDefaultCloseOperation() { return defaultCloseOperation; }
    public javax.swing.JRootPane getRootPane() { return rootPane; }
    public java.awt.Container getContentPane() { return rootPane.getContentPane(); }
    public void setContentPane(java.awt.Container contentPane) { rootPane.setContentPane(contentPane); }
    public void setJMenuBar(javax.swing.JMenuBar menu) { menuBar = menu; }
    public javax.swing.JMenuBar getJMenuBar() { return menuBar; }
    public void setGlassPane(java.awt.Component glass) {}
    public java.awt.Component getGlassPane() { return null; }
    public void setLayeredPane(javax.swing.JLayeredPane layeredPane) {}
    public javax.swing.JLayeredPane getLayeredPane() { return null; }
}
