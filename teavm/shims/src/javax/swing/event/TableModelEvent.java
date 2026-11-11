package javax.swing.event;
/** Minimal javax.swing.event.TableModelEvent. */
public class TableModelEvent extends java.util.EventObject {
    public static final int INSERT = 1;
    public static final int UPDATE = 0;
    public static final int DELETE = -1;
    public static final int HEADER_ROW = -1;
    public static final int ALL_COLUMNS = -1;
    private final int type, firstRow, lastRow, column;
    public TableModelEvent(javax.swing.table.TableModel source) { super(source); type = UPDATE; firstRow = 0; lastRow = Integer.MAX_VALUE; column = ALL_COLUMNS; }
    public TableModelEvent(javax.swing.table.TableModel source, int firstRow, int lastRow) { super(source); type = UPDATE; this.firstRow = firstRow; this.lastRow = lastRow; column = ALL_COLUMNS; }
    public TableModelEvent(javax.swing.table.TableModel source, int firstRow, int lastRow, int column) { super(source); type = UPDATE; this.firstRow = firstRow; this.lastRow = lastRow; this.column = column; }
    public TableModelEvent(javax.swing.table.TableModel source, int firstRow, int lastRow, int column, int type) { super(source); this.firstRow = firstRow; this.lastRow = lastRow; this.column = column; this.type = type; }
    public int getFirstRow() { return firstRow; }
    public int getLastRow() { return lastRow; }
    public int getColumn() { return column; }
    public int getType() { return type; }
}
