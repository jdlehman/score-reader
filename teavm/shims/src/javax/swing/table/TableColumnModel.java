package javax.swing.table;
/** Minimal javax.swing.table.TableColumnModel. */
public interface TableColumnModel {
    void addColumn(javax.swing.table.TableColumn aColumn);
    void removeColumn(javax.swing.table.TableColumn column);
    void moveColumn(int columnIndex, int newIndex);
    void setColumnMargin(int newMargin);
    int getColumnCount();
    java.util.Enumeration<javax.swing.table.TableColumn> getColumns();
    int getColumnIndex(Object columnIdentifier);
    javax.swing.table.TableColumn getColumn(int columnIndex);
    int getColumnMargin();
    int getSelectedColumnCount();
    int[] getSelectedColumns();
    void setSelectionModel(javax.swing.ListSelectionModel newModel);
    javax.swing.ListSelectionModel getSelectionModel();
    boolean getColumnSelectionAllowed();
    void setColumnSelectionAllowed(boolean flag);
    int getTotalColumnWidth();
    void addColumnModelListener(javax.swing.event.TableColumnModelListener x);
    void removeColumnModelListener(javax.swing.event.TableColumnModelListener x);
}
