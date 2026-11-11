package javax.swing.table;
/** Minimal javax.swing.table.TableCellEditor. */
public interface TableCellEditor extends javax.swing.CellEditor {
    java.awt.Component getTableCellEditorComponent(javax.swing.JTable table, Object value, boolean isSelected, int row, int column);
}
