package javax.swing;
/** Minimal javax.swing.JCheckBox. */
public class JCheckBox extends JToggleButton {
    public JCheckBox() {}
    public JCheckBox(String text) { this.text = text; }
    public JCheckBox(String text, boolean selected) { this.text = text; this.selected = selected; }
    public JCheckBox(Icon icon) { this.icon = icon; }
    public JCheckBox(Icon icon, boolean selected) { this.icon = icon; this.selected = selected; }
    public JCheckBox(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JCheckBox(String text, Icon icon, boolean selected) {
        this.text = text; this.icon = icon; this.selected = selected;
    }
    public JCheckBox(Action a) {}
}
