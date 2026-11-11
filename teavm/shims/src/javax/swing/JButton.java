package javax.swing;
/** Minimal javax.swing.JButton. */
public class JButton extends AbstractButton {
    public JButton() {}
    public JButton(String text) { this.text = text; }
    public JButton(Icon icon) { this.icon = icon; }
    public JButton(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JButton(Action a) {}
    public boolean isDefaultButton() { return false; }
    public boolean isDefaultCapable() { return false; }
    public void setDefaultCapable(boolean b) {}
}
