package javax.swing.table;
/** Minimal javax.swing.table.TableCellRenderer. */
public interface TableCellRenderer {
    java.awt.Component getTableCellRendererComponent(javax.swing.JTable table, Object value, boolean isSelected, boolean hasFocus, int row, int column);
}
