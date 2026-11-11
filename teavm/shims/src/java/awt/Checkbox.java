package java.awt;
import java.awt.event.ItemListener;
/** Minimal java.awt.Checkbox. */
public class Checkbox extends Component implements ItemSelectable {
    private String label = "";
    private boolean state;
    private CheckboxGroup group;
    public Checkbox() {}
    public Checkbox(String label) { this.label = label; }
    public Checkbox(String label, boolean state) { this.label = label; this.state = state; }
    public Checkbox(String label, boolean state, CheckboxGroup group) { this.label = label; this.state = state; this.group = group; }
    public Checkbox(String label, CheckboxGroup group, boolean state) { this.label = label; this.group = group; this.state = state; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public boolean getState() { return state; }
    public void setState(boolean state) { this.state = state; }
    public CheckboxGroup getCheckboxGroup() { return group; }
    public void setCheckboxGroup(CheckboxGroup g) { group = g; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public Object[] getSelectedObjects() { return state ? new Object[]{ label } : null; }
}
