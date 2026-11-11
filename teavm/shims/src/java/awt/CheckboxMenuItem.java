package java.awt;
import java.awt.event.*;
/** Minimal java.awt.CheckboxMenuItem. */
public class CheckboxMenuItem extends MenuItem implements ItemSelectable {
    protected boolean state;
    public CheckboxMenuItem() {}
    public CheckboxMenuItem(String label) { super(label); }
    public CheckboxMenuItem(String label, boolean state) { super(label); this.state = state; }
    public boolean getState() { return state; }
    public void setState(boolean state) { this.state = state; }
    public Object[] getSelectedObjects() { return state ? new Object[]{label} : new Object[0]; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public ItemListener[] getItemListeners() { return new ItemListener[0]; }
}
