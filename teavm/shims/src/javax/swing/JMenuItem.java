package javax.swing;
/** Minimal javax.swing.JMenuItem. */
public class JMenuItem extends AbstractButton {
    public JMenuItem() {}
    public JMenuItem(String text) { this.text = text; }
    public JMenuItem(Icon icon) { this.icon = icon; }
    public JMenuItem(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JMenuItem(String text, int mnemonic) { this.text = text; this.mnemonic = mnemonic; }
    public JMenuItem(Action a) {}
    public void setAccelerator(KeyStroke keyStroke) {}
    public KeyStroke getAccelerator() { return null; }
    public void setArmed(boolean b) {}
    public boolean isArmed() { return false; }
}
