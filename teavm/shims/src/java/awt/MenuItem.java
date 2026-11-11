package java.awt;
import java.awt.event.*;
/** Minimal java.awt.MenuItem. */
public class MenuItem extends MenuComponent implements java.io.Serializable {
    protected String label;
    protected boolean enabled = true;
    protected String actionCommand;
    public MenuItem() {}
    public MenuItem(String label) { this.label = label; }
    public MenuItem(String label, MenuShortcut s) { this.label = label; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean b) { enabled = b; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String cmd) { actionCommand = cmd; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
    public void setShortcut(MenuShortcut s) {}
    public MenuShortcut getShortcut() { return null; }
    public void deleteShortcut() {}
}
