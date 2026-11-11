package javax.swing;
/** Minimal javax.swing.JTable. */
public class JTable extends JComponent {
    public static final int AUTO_RESIZE_OFF = 0;
    public static final int AUTO_RESIZE_NEXT_COLUMN = 1;
    public static final int AUTO_RESIZE_SUBSEQUENT_COLUMNS = 2;
    public static final int AUTO_RESIZE_LAST_COLUMN = 3;
    public static final int AUTO_RESIZE_ALL_COLUMNS = 4;
    private javax.swing.table.TableModel model;
    private int autoResizeMode = AUTO_RESIZE_SUBSEQUENT_COLUMNS;
    private int selectedRow = -1, selectedColumn = -1;
    public JTable() { this(new javax.swing.table.DefaultTableModel()); }
    public JTable(javax.swing.table.TableModel dm) { model = dm; }
    public JTable(int numRows, int numColumns) { this(new javax.swing.table.DefaultTableModel(numRows, numColumns)); }
    public JTable(Object[][] rowData, Object[] columnNames) { this(new javax.swing.table.DefaultTableModel(rowData, columnNames)); }
    public javax.swing.table.TableModel getModel() { return model; }
    public void setModel(javax.swing.table.TableModel dataModel) { model = dataModel; }
    public int getRowCount() { return model == null ? 0 : model.getRowCount(); }
    public int getColumnCount() { return model == null ? 0 : model.getColumnCount(); }
    public String getColumnName(int column) { return model.getColumnName(column); }
    public Object getValueAt(int row, int column) { return model.getValueAt(row, column); }
    public void setValueAt(Object aValue, int row, int column) { model.setValueAt(aValue, row, column); }
    public boolean isCellEditable(int row, int column) { return model.isCellEditable(row, column); }
    public int getSelectedRow() { return selectedRow; }
    public int getSelectedColumn() { return selectedColumn; }
    public int[] getSelectedRows() { return selectedRow < 0 ? new int[0] : new int[]{ selectedRow }; }
    public int[] getSelectedColumns() { return selectedColumn < 0 ? new int[0] : new int[]{ selectedColumn }; }
    public void setRowSelectionInterval(int index0, int index1) { selectedRow = index0; }
    public void setColumnSelectionInterval(int index0, int index1) { selectedColumn = index0; }
    public void clearSelection() { selectedRow = -1; selectedColumn = -1; }
    public javax.swing.table.TableColumnModel getColumnModel() { return null; }
    public void setColumnModel(javax.swing.table.TableColumnModel columnModel) {}
    public int getAutoResizeMode() { return autoResizeMode; }
    public void setAutoResizeMode(int mode) { autoResizeMode = mode; }
    public void setRowHeight(int rowHeight) {}
    public int getRowHeight() { return 16; }
    public void setRowHeight(int row, int rowHeight) {}
    public int getRowHeight(int row) { return 16; }
    public boolean getRowSelectionAllowed() { return true; }
    public void setRowSelectionAllowed(boolean rowSelectionAllowed) {}
    public boolean getColumnSelectionAllowed() { return false; }
    public void setColumnSelectionAllowed(boolean columnSelectionAllowed) {}
    public void setSelectionMode(int selectionMode) {}
    public int getSelectionMode() { return ListSelectionModel.MULTIPLE_INTERVAL_SELECTION; }
    public void addRowSelectionInterval(int index0, int index1) {}
    public javax.swing.table.TableCellRenderer getDefaultRenderer(Class<?> columnClass) { return null; }
    public void setDefaultRenderer(Class<?> columnClass, javax.swing.table.TableCellRenderer renderer) {}
    public javax.swing.table.TableCellEditor getDefaultEditor(Class<?> columnClass) { return null; }
    public void setDefaultEditor(Class<?> columnClass, javax.swing.table.TableCellEditor editor) {}
    public javax.swing.table.TableCellRenderer getCellRenderer(int row, int column) { return null; }
    public javax.swing.table.TableCellEditor getCellEditor(int row, int column) { return null; }
    public void setShowGrid(boolean showGrid) {}
    public void setShowHorizontalLines(boolean showHorizontalLines) {}
    public void setShowVerticalLines(boolean showVerticalLines) {}
    public void setIntercellSpacing(java.awt.Dimension intercellSpacing) {}
    public java.awt.Dimension getIntercellSpacing() { return new java.awt.Dimension(1, 1); }
    public void setTableHeader(javax.swing.table.JTableHeader tableHeader) {}
    public javax.swing.table.JTableHeader getTableHeader() { return null; }
    public void setAutoCreateRowSorter(boolean autoCreateRowSorter) {}
    public boolean getAutoCreateRowSorter() { return false; }
}
