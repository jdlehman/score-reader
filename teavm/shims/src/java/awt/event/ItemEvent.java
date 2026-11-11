package java.awt.event;
import java.awt.ItemSelectable;
/** Minimal java.awt.event.ItemEvent. */
public class ItemEvent extends java.awt.AWTEvent {
    public static final int ITEM_FIRST = 701;
    public static final int ITEM_LAST = 701;
    public static final int ITEM_STATE_CHANGED = ITEM_FIRST;
    public static final int SELECTED = 1;
    public static final int DESELECTED = 2;
    protected ItemSelectable itemSelectable;
    protected Object item;
    protected int stateChange;
    public ItemEvent(ItemSelectable source, int id, Object item, int stateChange) {
        super(source, id); itemSelectable = source; this.item = item; this.stateChange = stateChange;
    }
    public ItemSelectable getItemSelectable() { return itemSelectable; }
    public Object getItem() { return item; }
    public int getStateChange() { return stateChange; }
}
