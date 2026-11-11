package javax.swing.table;
/** Minimal javax.swing.table.AbstractTableModel. */
public abstract class AbstractTableModel implements TableModel, java.io.Serializable {
    protected javax.swing.event.EventListenerList listenerList = new javax.swing.event.EventListenerList();
    public String getColumnName(int column) { return "ABCDEFGHIJKLMNOPQRSTUVWXYZ".substring(column % 26, column % 26 + 1); }
    public Class<?> getColumnClass(int columnIndex) { return Object.class; }
    public boolean isCellEditable(int rowIndex, int columnIndex) { return false; }
    public void setValueAt(Object aValue, int rowIndex, int columnIndex) {}
    public void addTableModelListener(javax.swing.event.TableModelListener l) { listenerList.add(javax.swing.event.TableModelListener.class, l); }
    public void removeTableModelListener(javax.swing.event.TableModelListener l) { listenerList.remove(javax.swing.event.TableModelListener.class, l); }
    public javax.swing.event.TableModelListener[] getTableModelListeners() { return listenerList.getListeners(javax.swing.event.TableModelListener.class); }
    public void fireTableDataChanged() {}
    public void fireTableStructureChanged() {}
    public void fireTableRowsInserted(int firstRow, int lastRow) {}
    public void fireTableRowsDeleted(int firstRow, int lastRow) {}
    public void fireTableRowsUpdated(int firstRow, int lastRow) {}
    public void fireTableCellUpdated(int row, int column) {}
    public void fireTableChanged(javax.swing.event.TableModelEvent e) {}
}
