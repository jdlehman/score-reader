package java.awt;
/** Minimal java.awt.CheckboxGroup. */
public class CheckboxGroup implements java.io.Serializable {
    private Checkbox selected;
    public Checkbox getSelectedCheckbox() { return selected; }
    public void setSelectedCheckbox(Checkbox box) { selected = box; }
    public String toString() { return "CheckboxGroup"; }
}
