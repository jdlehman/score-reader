package java.awt;
import java.awt.event.ItemListener;
/** Minimal java.awt.Choice. */
public class Choice extends Component implements ItemSelectable {
    private final java.util.List<String> items = new java.util.ArrayList<>();
    private int selected;
    public Choice() {}
    public int getItemCount() { return items.size(); }
    public String getItem(int index) { return items.get(index); }
    public void add(String item) { items.add(item); }
    public void addItem(String item) { add(item); }
    public void insert(String item, int index) { items.add(index, item); }
    public void remove(String item) { items.remove(item); }
    public void remove(int index) { items.remove(index); }
    public void removeAll() { items.clear(); }
    public int getSelectedIndex() { return selected; }
    public String getSelectedItem() { return items.isEmpty() ? null : items.get(selected); }
    public void select(int pos) { selected = pos; }
    public void select(String str) { int i = items.indexOf(str); if (i >= 0) selected = i; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public Object[] getSelectedObjects() { return items.isEmpty() ? null : new Object[]{ getSelectedItem() }; }
}
