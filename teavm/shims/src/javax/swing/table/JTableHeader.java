package javax.swing.table;
/** Minimal javax.swing.table.JTableHeader. */
public class JTableHeader extends javax.swing.JComponent {
    private javax.swing.JTable table;
    private TableColumnModel columnModel;
    public JTableHeader() {}
    public JTableHeader(TableColumnModel cm) { columnModel = cm; }
    public javax.swing.JTable getTable() { return table; }
    public void setTable(javax.swing.JTable table) { this.table = table; }
    public TableColumnModel getColumnModel() { return columnModel; }
    public void setColumnModel(TableColumnModel columnModel) { this.columnModel = columnModel; }
    public void setReorderingAllowed(boolean reorderingAllowed) {}
    public boolean getReorderingAllowed() { return true; }
    public void setResizingAllowed(boolean resizingAllowed) {}
    public boolean getResizingAllowed() { return true; }
    public void setUpdateTableInRealTime(boolean flag) {}
    public boolean getUpdateTableInRealTime() { return true; }
}
