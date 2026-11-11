package javax.swing;
import java.awt.event.*;
/** Minimal javax.swing.AbstractButton. */
public abstract class AbstractButton extends JComponent implements java.awt.ItemSelectable, SwingConstants {
    protected String text;
    protected Icon icon;
    protected boolean selected;
    protected String actionCommand;
    protected int mnemonic;
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
    public Icon getIcon() { return icon; }
    public void setIcon(Icon icon) { this.icon = icon; }
    public boolean isSelected() { return selected; }
    public void setSelected(boolean b) { selected = b; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String cmd) { actionCommand = cmd; }
    public int getMnemonic() { return mnemonic; }
    public void setMnemonic(int m) { mnemonic = m; }
    public void setMnemonic(char m) { mnemonic = m; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public ItemListener[] getItemListeners() { return new ItemListener[0]; }
    public Object[] getSelectedObjects() { return selected ? new Object[]{text} : new Object[0]; }
    public void doClick() {}
    public void doClick(int pressTime) {}
    public void setAction(Action a) {}
    public Action getAction() { return null; }
    public void setHorizontalAlignment(int a) {}
    public int getHorizontalAlignment() { return CENTER; }
    public void setVerticalAlignment(int a) {}
    public int getVerticalAlignment() { return CENTER; }
    public void setDisplayedMnemonicIndex(int i) {}
    public int getDisplayedMnemonicIndex() { return -1; }
    public void setIconTextGap(int g) {}
    public int getIconTextGap() { return 0; }
    public void setRolloverEnabled(boolean b) {}
    public boolean isRolloverEnabled() { return false; }
    public void setBorderPainted(boolean b) {}
    public boolean isBorderPainted() { return false; }
    public void setContentAreaFilled(boolean b) {}
    public boolean isContentAreaFilled() { return false; }
    public void setFocusPainted(boolean b) {}
    public boolean isFocusPainted() { return false; }
}
