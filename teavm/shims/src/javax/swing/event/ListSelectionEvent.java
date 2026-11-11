package javax.swing.event;
/** Minimal javax.swing.event.ListSelectionEvent. */
public class ListSelectionEvent extends java.util.EventObject {
    private final int firstIndex, lastIndex;
    private final boolean isAdjusting;
    public ListSelectionEvent(Object source, int firstIndex, int lastIndex, boolean isAdjusting) {
        super(source); this.firstIndex = firstIndex; this.lastIndex = lastIndex; this.isAdjusting = isAdjusting;
    }
    public int getFirstIndex() { return firstIndex; }
    public int getLastIndex() { return lastIndex; }
    public boolean getValueIsAdjusting() { return isAdjusting; }
}
