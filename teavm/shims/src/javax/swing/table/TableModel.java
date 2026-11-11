package javax.swing.table;
/** Minimal javax.swing.table.TableModel. */
public interface TableModel {
    int getRowCount();
    int getColumnCount();
    String getColumnName(int columnIndex);
    Class<?> getColumnClass(int columnIndex);
    boolean isCellEditable(int rowIndex, int columnIndex);
    Object getValueAt(int rowIndex, int columnIndex);
    void setValueAt(Object aValue, int rowIndex, int columnIndex);
    void addTableModelListener(javax.swing.event.TableModelListener l);
    void removeTableModelListener(javax.swing.event.TableModelListener l);
}
