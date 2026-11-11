package javax.swing;
/** Minimal javax.swing.JToggleButton. */
public class JToggleButton extends AbstractButton {
    public JToggleButton() {}
    public JToggleButton(String text) { this.text = text; }
    public JToggleButton(Icon icon) { this.icon = icon; }
    public JToggleButton(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JToggleButton(String text, boolean selected) { this.text = text; this.selected = selected; }
    public JToggleButton(Action a) {}
}
