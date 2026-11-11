package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JLabel. */
public class JLabel extends JComponent implements SwingConstants {
    protected String text;
    protected Icon icon;
    protected int horizontalAlignment = LEADING, verticalAlignment = CENTER;
    protected Component labelFor;
    public JLabel() {}
    public JLabel(String text) { this.text = text; }
    public JLabel(String text, int horizontalAlignment) { this.text = text; this.horizontalAlignment = horizontalAlignment; }
    public JLabel(Icon image) { icon = image; }
    public JLabel(Icon image, int horizontalAlignment) { icon = image; this.horizontalAlignment = horizontalAlignment; }
    public JLabel(String text, Icon icon, int horizontalAlignment) {
        this.text = text; this.icon = icon; this.horizontalAlignment = horizontalAlignment;
    }
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
    public Icon getIcon() { return icon; }
    public void setIcon(Icon icon) { this.icon = icon; }
    public int getHorizontalAlignment() { return horizontalAlignment; }
    public void setHorizontalAlignment(int a) { horizontalAlignment = a; }
    public int getVerticalAlignment() { return verticalAlignment; }
    public void setVerticalAlignment(int a) { verticalAlignment = a; }
    public Component getLabelFor() { return labelFor; }
    public void setLabelFor(Component c) { labelFor = c; }
    public Icon getDisabledIcon() { return null; }
    public void setDisabledIcon(Icon icon) {}
    public int getDisplayedMnemonic() { return 0; }
    public void setDisplayedMnemonic(int m) {}
    public void setDisplayedMnemonic(char m) {}
    public int getDisplayedMnemonicIndex() { return -1; }
    public void setDisplayedMnemonicIndex(int i) {}
    public void setIconTextGap(int g) {}
    public int getIconTextGap() { return 0; }
}
