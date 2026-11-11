package javax.swing.event;
/** Minimal javax.swing.event.TableColumnModelEvent. */
public class TableColumnModelEvent extends java.util.EventObject {
    private final int fromIndex, toIndex;
    public TableColumnModelEvent(javax.swing.table.TableColumnModel source, int from, int to) {
        super(source); fromIndex = from; toIndex = to;
    }
    public int getFromIndex() { return fromIndex; }
    public int getToIndex() { return toIndex; }
}
