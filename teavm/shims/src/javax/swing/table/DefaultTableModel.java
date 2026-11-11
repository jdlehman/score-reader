package javax.swing.table;
/** Minimal javax.swing.table.DefaultTableModel. */
public class DefaultTableModel extends AbstractTableModel {
    private java.util.Vector<java.util.Vector<Object>> data = new java.util.Vector<>();
    private java.util.Vector<Object> columnIdentifiers = new java.util.Vector<>();
    public DefaultTableModel() {}
    public DefaultTableModel(Object[][] data, Object[] columnNames) {
        for (Object[] row : data) { java.util.Vector<Object> v = new java.util.Vector<>(); for (Object o : row) v.add(o); this.data.add(v); }
        for (Object c : columnNames) columnIdentifiers.add(c);
    }
    public DefaultTableModel(java.util.Vector<?> data, java.util.Vector<?> columnNames) {}
    public DefaultTableModel(int rowCount, int columnCount) { for (int i = 0; i < rowCount; i++) { java.util.Vector<Object> v = new java.util.Vector<>(); for (int j = 0; j < columnCount; j++) v.add(null); data.add(v); } for (int j = 0; j < columnCount; j++) columnIdentifiers.add(""); }
    public int getRowCount() { return data.size(); }
    public int getColumnCount() { return columnIdentifiers.size(); }
    public String getColumnName(int column) { Object c = columnIdentifiers.get(column); return c == null ? "" : c.toString(); }
    public Object getValueAt(int row, int column) { return data.get(row).get(column); }
    public void setValueAt(Object aValue, int row, int column) { data.get(row).set(column, aValue); fireTableCellUpdated(row, column); }
    public void addRow(Object[] rowData) { java.util.Vector<Object> v = new java.util.Vector<>(); for (Object o : rowData) v.add(o); data.add(v); }
    public void addRow(java.util.Vector<?> rowData) { java.util.Vector<Object> v = new java.util.Vector<>(); v.addAll(rowData); data.add(v); }
    public void removeRow(int row) { data.remove(row); }
    public void addColumn(Object columnName) { columnIdentifiers.add(columnName); }
    public void setColumnIdentifiers(Object[] columnIdentifiers) { this.columnIdentifiers.clear(); for (Object c : columnIdentifiers) this.columnIdentifiers.add(c); }
    public void setColumnIdentifiers(java.util.Vector<?> columnIdentifiers) { this.columnIdentifiers.clear(); this.columnIdentifiers.addAll(columnIdentifiers); }
    public void setRowCount(int rowCount) { while (data.size() > rowCount) data.remove(data.size() - 1); while (data.size() < rowCount) { java.util.Vector<Object> v = new java.util.Vector<>(); for (int j = 0; j < getColumnCount(); j++) v.add(null); data.add(v); } }
}
