#!/usr/bin/env python3
"""Generate round-6 Swing stub sources (file chooser, lists, tables, dialogs).

Round-6 follow-up to gen_swing2.py: these classes were unblocked for
analysis once Frame/JPanel shims landed (round 4), and ij + Audiveris UI
code references them. Same conventions: minimal headless stubs, only the
API surface referenced by ij / Audiveris / appframework. ROOT is shims/src.
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
SW = "javax/swing/"

FILES = {}

FILES[SW + "AbstractAction.java"] = """package javax.swing;
import java.beans.PropertyChangeListener;
/** Minimal javax.swing.AbstractAction. */
public abstract class AbstractAction implements Action, Cloneable, java.io.Serializable {
    private boolean enabled = true;
    private final java.util.Map<String, Object> values = new java.util.HashMap<>();
    public AbstractAction() {}
    public AbstractAction(String name) { putValue(NAME, name); }
    public AbstractAction(String name, Icon icon) { putValue(NAME, name); putValue(SMALL_ICON, icon); }
    public Object getValue(String key) { return values.get(key); }
    public void putValue(String key, Object newValue) { values.put(key, newValue); }
    public void setEnabled(boolean newValue) { enabled = newValue; }
    public boolean isEnabled() { return enabled; }
    public Object[] getKeys() { return values.keySet().toArray(); }
    public void addPropertyChangeListener(PropertyChangeListener listener) {}
    public void removePropertyChangeListener(PropertyChangeListener listener) {}
    public abstract void actionPerformed(java.awt.event.ActionEvent e);
}
"""

FILES[SW + "ListModel.java"] = """package javax.swing;
/** Minimal javax.swing.ListModel. */
public interface ListModel<E> {
    int getSize();
    E getElementAt(int index);
    void addListDataListener(javax.swing.event.ListDataListener l);
    void removeListDataListener(javax.swing.event.ListDataListener l);
}
"""

FILES[SW + "AbstractListModel.java"] = """package javax.swing;
/** Minimal javax.swing.AbstractListModel. */
public abstract class AbstractListModel<E> implements ListModel<E>, java.io.Serializable {
    protected javax.swing.event.EventListenerList listenerList = new javax.swing.event.EventListenerList();
    public void addListDataListener(javax.swing.event.ListDataListener l) { listenerList.add(javax.swing.event.ListDataListener.class, l); }
    public void removeListDataListener(javax.swing.event.ListDataListener l) { listenerList.remove(javax.swing.event.ListDataListener.class, l); }
    public javax.swing.event.ListDataListener[] getListDataListeners() { return listenerList.getListeners(javax.swing.event.ListDataListener.class); }
    protected void fireContentsChanged(Object source, int index0, int index1) {}
    protected void fireIntervalAdded(Object source, int index0, int index1) {}
    protected void fireIntervalRemoved(Object source, int index0, int index1) {}
}
"""

FILES[SW + "DefaultListModel.java"] = """package javax.swing;
/** Minimal javax.swing.DefaultListModel. */
public class DefaultListModel<E> extends AbstractListModel<E> {
    private final java.util.List<E> delegate = new java.util.ArrayList<>();
    public int getSize() { return delegate.size(); }
    public E getElementAt(int index) { return delegate.get(index); }
    public void addElement(E element) { delegate.add(element); fireIntervalAdded(this, delegate.size() - 1, delegate.size() - 1); }
    public void insertElementAt(E element, int index) { delegate.add(index, element); fireIntervalAdded(this, index, index); }
    public boolean removeElement(Object obj) { int i = delegate.indexOf(obj); if (i < 0) return false; delegate.remove(i); fireIntervalRemoved(this, i, i); return true; }
    public void removeElementAt(int index) { delegate.remove(index); fireIntervalRemoved(this, index, index); }
    public void removeAllElements() { int n = delegate.size(); delegate.clear(); if (n > 0) fireIntervalRemoved(this, 0, n - 1); }
    public void clear() { removeAllElements(); }
    public void add(int index, E element) { insertElementAt(element, index); }
    public E remove(int index) { E e = delegate.remove(index); fireIntervalRemoved(this, index, index); return e; }
    public boolean remove(Object o) { return removeElement(o); }
    public E get(int index) { return delegate.get(index); }
    public E set(int index, E element) { E old = delegate.set(index, element); fireContentsChanged(this, index, index); return old; }
    public void setElementAt(E element, int index) { set(index, element); }
    public boolean contains(Object elem) { return delegate.contains(elem); }
    public int indexOf(Object elem) { return delegate.indexOf(elem); }
    public int indexOf(Object elem, int index) { return delegate.indexOf(elem); }
    public int lastIndexOf(Object elem) { return delegate.lastIndexOf(elem); }
    public E firstElement() { return delegate.get(0); }
    public E lastElement() { return delegate.get(delegate.size() - 1); }
    public boolean isEmpty() { return delegate.isEmpty(); }
    public int size() { return delegate.size(); }
    public Object[] toArray() { return delegate.toArray(); }
    public <T> T[] toArray(T[] a) { return delegate.toArray(a); }
    public java.util.Enumeration<E> elements() { return java.util.Collections.enumeration(delegate); }
    public void copyInto(Object[] anArray) { delegate.toArray(anArray); }
    public void setSize(int newSize) { while (delegate.size() > newSize) delegate.remove(delegate.size() - 1); while (delegate.size() < newSize) delegate.add(null); }
    public void trimToSize() {}
    public void ensureCapacity(int minCapacity) {}
}
"""

FILES[SW + "ListSelectionModel.java"] = """package javax.swing;
/** Minimal javax.swing.ListSelectionModel. */
public interface ListSelectionModel {
    int SINGLE_SELECTION = 0;
    int SINGLE_INTERVAL_SELECTION = 1;
    int MULTIPLE_INTERVAL_SELECTION = 2;
    void setSelectionInterval(int index0, int index1);
    void addSelectionInterval(int index0, int index1);
    void removeSelectionInterval(int index0, int index1);
    int getMinSelectionIndex();
    int getMaxSelectionIndex();
    boolean isSelectedIndex(int index);
    int getAnchorSelectionIndex();
    void setAnchorSelectionIndex(int index);
    int getLeadSelectionIndex();
    void setLeadSelectionIndex(int index);
    void clearSelection();
    boolean isSelectionEmpty();
    void insertIndexInterval(int index, int length, boolean before);
    void removeIndexInterval(int index0, int index1);
    void setValueIsAdjusting(boolean valueIsAdjusting);
    boolean getValueIsAdjusting();
    void setSelectionMode(int selectionMode);
    int getSelectionMode();
    void addListSelectionListener(javax.swing.event.ListSelectionListener l);
    void removeListSelectionListener(javax.swing.event.ListSelectionListener l);
}
"""

FILES[SW + "JList.java"] = """package javax.swing;
/** Minimal javax.swing.JList. */
public class JList<E> extends JComponent {
    public static final int VERTICAL = 0;
    public static final int VERTICAL_WRAP = 1;
    public static final int HORIZONTAL_WRAP = 2;
    private ListModel<E> model;
    private int selectionMode = ListSelectionModel.SINGLE_SELECTION;
    private int selectedIndex = -1;
    private int visibleRowCount = 8;
    private ListCellRenderer<? super E> cellRenderer;
    public JList() { this(new DefaultListModel<E>()); }
    public JList(ListModel<E> dataModel) { model = dataModel; }
    public JList(E[] listData) { DefaultListModel<E> m = new DefaultListModel<>(); for (E e : listData) m.addElement(e); model = m; }
    public JList(java.util.Vector<? extends E> listData) { DefaultListModel<E> m = new DefaultListModel<>(); for (E e : listData) m.addElement(e); model = m; }
    public ListModel<E> getModel() { return model; }
    public void setModel(ListModel<E> model) { this.model = model; }
    public void setListData(E[] listData) { DefaultListModel<E> m = new DefaultListModel<>(); for (E e : listData) m.addElement(e); model = m; }
    public void setListData(java.util.Vector<? extends E> listData) { DefaultListModel<E> m = new DefaultListModel<>(); for (E e : listData) m.addElement(e); model = m; }
    public int getSelectionMode() { return selectionMode; }
    public void setSelectionMode(int selectionMode) { this.selectionMode = selectionMode; }
    public int getSelectedIndex() { return selectedIndex; }
    public void setSelectedIndex(int index) { selectedIndex = index; }
    public void setSelectedIndices(int[] indices) { selectedIndex = (indices == null || indices.length == 0) ? -1 : indices[0]; }
    public int[] getSelectedIndices() { return selectedIndex < 0 ? new int[0] : new int[]{ selectedIndex }; }
    public E getSelectedValue() { return (selectedIndex < 0 || model == null) ? null : model.getElementAt(selectedIndex); }
    public java.util.List<E> getSelectedValuesList() { E v = getSelectedValue(); return v == null ? new java.util.ArrayList<>() : java.util.Collections.singletonList(v); }
    public boolean isSelectionEmpty() { return selectedIndex < 0; }
    public void clearSelection() { selectedIndex = -1; }
    public int getVisibleRowCount() { return visibleRowCount; }
    public void setVisibleRowCount(int visibleRowCount) { this.visibleRowCount = visibleRowCount; }
    public ListCellRenderer<? super E> getCellRenderer() { return cellRenderer; }
    public void setCellRenderer(ListCellRenderer<? super E> cellRenderer) { this.cellRenderer = cellRenderer; }
    public ListSelectionModel getSelectionModel() { return null; }
    public void setSelectionModel(ListSelectionModel selectionModel) {}
    public void addListSelectionListener(javax.swing.event.ListSelectionListener listener) {}
    public void removeListSelectionListener(javax.swing.event.ListSelectionListener listener) {}
    public int locationToIndex(java.awt.Point location) { return -1; }
    public int getFirstVisibleIndex() { return 0; }
    public int getLastVisibleIndex() { return model == null ? -1 : model.getSize() - 1; }
    public void ensureIndexIsVisible(int index) {}
    public void setFixedCellHeight(int height) {}
    public void setFixedCellWidth(int width) {}
    public int getFixedCellHeight() { return -1; }
    public int getFixedCellWidth() { return -1; }
    public void setLayoutOrientation(int layoutOrientation) {}
    public int getLayoutOrientation() { return VERTICAL; }
}
"""

FILES[SW + "ListCellRenderer.java"] = """package javax.swing;
/** Minimal javax.swing.ListCellRenderer. */
public interface ListCellRenderer<E> {
    java.awt.Component getListCellRendererComponent(JList<? extends E> list, E value, int index, boolean isSelected, boolean cellHasFocus);
}
"""

FILES[SW + "table/TableModel.java"] = """package javax.swing.table;
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
"""

FILES[SW + "table/AbstractTableModel.java"] = """package javax.swing.table;
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
"""

FILES[SW + "table/DefaultTableModel.java"] = """package javax.swing.table;
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
"""

FILES[SW + "table/TableColumnModel.java"] = """package javax.swing.table;
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
"""

FILES[SW + "table/TableColumn.java"] = """package javax.swing.table;
/** Minimal javax.swing.table.TableColumn. */
public class TableColumn implements java.io.Serializable {
    public static final int DEFAULT_WIDTH = 75;
    public static final int MIN_WIDTH = 15;
    public static final int MAX_WIDTH = Integer.MAX_VALUE;
    private int modelIndex, width = DEFAULT_WIDTH, minWidth = MIN_WIDTH, maxWidth = MAX_WIDTH, preferredWidth = DEFAULT_WIDTH;
    private Object identifier, headerValue;
    private boolean resizable = true;
    public TableColumn() {}
    public TableColumn(int modelIndex) { this.modelIndex = modelIndex; }
    public TableColumn(int modelIndex, int width) { this.modelIndex = modelIndex; this.width = width; }
    public TableColumn(int modelIndex, int width, javax.swing.table.TableCellRenderer cellRenderer, javax.swing.table.TableCellEditor cellEditor) { this.modelIndex = modelIndex; this.width = width; }
    public int getModelIndex() { return modelIndex; }
    public void setModelIndex(int modelIndex) { this.modelIndex = modelIndex; }
    public Object getIdentifier() { return identifier; }
    public void setIdentifier(Object identifier) { this.identifier = identifier; }
    public Object getHeaderValue() { return headerValue; }
    public void setHeaderValue(Object headerValue) { this.headerValue = headerValue; }
    public int getWidth() { return width; }
    public void setWidth(int width) { this.width = width; }
    public int getPreferredWidth() { return preferredWidth; }
    public void setPreferredWidth(int preferredWidth) { this.preferredWidth = preferredWidth; }
    public int getMinWidth() { return minWidth; }
    public void setMinWidth(int minWidth) { this.minWidth = minWidth; }
    public int getMaxWidth() { return maxWidth; }
    public void setMaxWidth(int maxWidth) { this.maxWidth = maxWidth; }
    public boolean getResizable() { return resizable; }
    public void setResizable(boolean isResizable) { resizable = isResizable; }
    public void sizeWidthToFit() {}
    public void addPropertyChangeListener(java.beans.PropertyChangeListener listener) {}
    public void removePropertyChangeListener(java.beans.PropertyChangeListener listener) {}
}
"""

FILES[SW + "table/TableCellRenderer.java"] = """package javax.swing.table;
/** Minimal javax.swing.table.TableCellRenderer. */
public interface TableCellRenderer {
    java.awt.Component getTableCellRendererComponent(javax.swing.JTable table, Object value, boolean isSelected, boolean hasFocus, int row, int column);
}
"""

FILES[SW + "table/TableCellEditor.java"] = """package javax.swing.table;
/** Minimal javax.swing.table.TableCellEditor. */
public interface TableCellEditor extends javax.swing.CellEditor {
    java.awt.Component getTableCellEditorComponent(javax.swing.JTable table, Object value, boolean isSelected, int row, int column);
}
"""

FILES[SW + "CellEditor.java"] = """package javax.swing;
/** Minimal javax.swing.CellEditor. */
public interface CellEditor {
    Object getCellEditorValue();
    boolean isCellEditable(java.util.EventObject anEvent);
    boolean shouldSelectCell(java.util.EventObject anEvent);
    boolean stopCellEditing();
    void cancelCellEditing();
    void addCellEditorListener(javax.swing.event.CellEditorListener l);
    void removeCellEditorListener(javax.swing.event.CellEditorListener l);
}
"""

FILES[SW + "JTable.java"] = """package javax.swing;
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
"""

FILES[SW + "table/JTableHeader.java"] = """package javax.swing.table;
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
"""

FILES[SW + "JFileChooser.java"] = """package javax.swing;
/** Minimal javax.swing.JFileChooser. */
public class JFileChooser extends JComponent {
    public static final int OPEN_DIALOG = 0;
    public static final int SAVE_DIALOG = 1;
    public static final int CUSTOM_DIALOG = 2;
    public static final int APPROVE_OPTION = 0;
    public static final int CANCEL_OPTION = 1;
    public static final int ERROR_OPTION = -1;
    public static final int FILES_ONLY = 0;
    public static final int DIRECTORIES_ONLY = 1;
    public static final int FILES_AND_DIRECTORIES = 2;
    private java.io.File selectedFile;
    private java.io.File[] selectedFiles = new java.io.File[0];
    private java.io.File currentDirectory;
    private int dialogType = OPEN_DIALOG;
    private int fileSelectionMode = FILES_ONLY;
    private boolean multiSelectionEnabled;
    private javax.swing.filechooser.FileFilter fileFilter;
    private String dialogTitle;
    public JFileChooser() {}
    public JFileChooser(String currentDirectoryPath) { currentDirectory = new java.io.File(currentDirectoryPath); }
    public JFileChooser(java.io.File currentDirectory) { this.currentDirectory = currentDirectory; }
    public int showOpenDialog(java.awt.Component parent) { return CANCEL_OPTION; }
    public int showSaveDialog(java.awt.Component parent) { return CANCEL_OPTION; }
    public int showDialog(java.awt.Component parent, String approveButtonText) { return CANCEL_OPTION; }
    public java.io.File getSelectedFile() { return selectedFile; }
    public void setSelectedFile(java.io.File file) { selectedFile = file; }
    public String getName(java.io.File f) { return (f == null) ? null : f.getName(); }
    public String getDescription(java.io.File f) { return getName(f); }
    public String getTypeDescription(java.io.File f) { return null; }
    public java.io.File[] getSelectedFiles() { return selectedFiles; }
    public void setSelectedFiles(java.io.File[] selectedFiles) { this.selectedFiles = selectedFiles; }
    public java.io.File getCurrentDirectory() { return currentDirectory; }
    public void setCurrentDirectory(java.io.File dir) { currentDirectory = dir; }
    public int getDialogType() { return dialogType; }
    public void setDialogType(int dialogType) { this.dialogType = dialogType; }
    public int getFileSelectionMode() { return fileSelectionMode; }
    public void setFileSelectionMode(int mode) { fileSelectionMode = mode; }
    public boolean isMultiSelectionEnabled() { return multiSelectionEnabled; }
    public void setMultiSelectionEnabled(boolean b) { multiSelectionEnabled = b; }
    public javax.swing.filechooser.FileFilter getFileFilter() { return fileFilter; }
    public void setFileFilter(javax.swing.filechooser.FileFilter filter) { fileFilter = filter; }
    public void addChoosableFileFilter(javax.swing.filechooser.FileFilter filter) {}
    public boolean removeChoosableFileFilter(javax.swing.filechooser.FileFilter f) { return false; }
    public javax.swing.filechooser.FileFilter[] getChoosableFileFilters() { return new javax.swing.filechooser.FileFilter[0]; }
    public void setAcceptAllFileFilterUsed(boolean b) {}
    public boolean isAcceptAllFileFilterUsed() { return true; }
    public String getDialogTitle() { return dialogTitle; }
    public void setDialogTitle(String dialogTitle) { this.dialogTitle = dialogTitle; }
    public void setApproveButtonText(String approveButtonText) {}
    public String getApproveButtonText() { return null; }
    public void rescanCurrentDirectory() {}
    public void setFileHidingEnabled(boolean b) {}
    public boolean isFileHidingEnabled() { return true; }
    public void setControlButtonsAreShown(boolean b) {}
    public boolean getControlButtonsAreShown() { return true; }
}
"""

FILES[SW + "filechooser/FileFilter.java"] = """package javax.swing.filechooser;
/** Minimal javax.swing.filechooser.FileFilter. */
public abstract class FileFilter {
    public abstract boolean accept(java.io.File f);
    public abstract String getDescription();
}
"""

FILES[SW + "JOptionPane.java"] = """package javax.swing;
/** Minimal javax.swing.JOptionPane. */
public class JOptionPane extends JComponent {
    public static final int DEFAULT_OPTION = -1;
    public static final int YES_NO_OPTION = 0;
    public static final int YES_NO_CANCEL_OPTION = 1;
    public static final int OK_CANCEL_OPTION = 2;
    public static final int YES_OPTION = 0;
    public static final int NO_OPTION = 1;
    public static final int CANCEL_OPTION = 2;
    public static final int OK_OPTION = 0;
    public static final int CLOSED_OPTION = -1;
    public static final int ERROR_MESSAGE = 0;
    public static final int INFORMATION_MESSAGE = 1;
    public static final int WARNING_MESSAGE = 2;
    public static final int QUESTION_MESSAGE = 3;
    public static final int PLAIN_MESSAGE = -1;
    public static final Object UNINITIALIZED_VALUE = "uninitializedValue";
    private Object message, messageType = QUESTION_MESSAGE, optionType = YES_NO_OPTION, value = UNINITIALIZED_VALUE;
    private Object[] options;
    private Object initialValue;
    public JOptionPane() {}
    public JOptionPane(Object message) { this.message = message; }
    public JOptionPane(Object message, int messageType) { this.message = message; this.messageType = messageType; }
    public JOptionPane(Object message, int messageType, int optionType) { this.message = message; this.messageType = messageType; this.optionType = optionType; }
    public JOptionPane(Object message, int messageType, int optionType, Icon icon) { this.message = message; this.messageType = messageType; this.optionType = optionType; }
    public JOptionPane(Object message, int messageType, int optionType, Icon icon, Object[] options) { this.message = message; this.messageType = messageType; this.optionType = optionType; this.options = options; }
    public JOptionPane(Object message, int messageType, int optionType, Icon icon, Object[] options, Object initialValue) { this.message = message; this.messageType = messageType; this.optionType = optionType; this.options = options; this.initialValue = initialValue; }
    public Object getMessage() { return message; }
    public void setMessage(Object newMessage) { message = newMessage; }
    public Object[] getOptions() { return options; }
    public void setOptions(Object[] newOptions) { options = newOptions; }
    public Object getInitialValue() { return initialValue; }
    public void setInitialValue(Object newInitialValue) { initialValue = newInitialValue; }
    public Object getValue() { return value; }
    public void setValue(Object newValue) { value = newValue; }
    public static String showInputDialog(Object message) { return null; }
    public static String showInputDialog(java.awt.Component parentComponent, Object message) { return null; }
    public static String showInputDialog(java.awt.Component parentComponent, Object message, String title, int messageType) { return null; }
    public static Object showInputDialog(java.awt.Component parentComponent, Object message, String title, int messageType, Icon icon, Object[] selectionValues, Object initialSelectionValue) { return null; }
    public static void showMessageDialog(java.awt.Component parentComponent, Object message) {}
    public static void showMessageDialog(java.awt.Component parentComponent, Object message, String title, int messageType) {}
    public static void showMessageDialog(java.awt.Component parentComponent, Object message, String title, int messageType, Icon icon) {}
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message) { return CLOSED_OPTION; }
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message, String title, int optionType) { return CLOSED_OPTION; }
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message, String title, int optionType, int messageType) { return CLOSED_OPTION; }
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message, String title, int optionType, int messageType, Icon icon) { return CLOSED_OPTION; }
    public static int showOptionDialog(java.awt.Component parentComponent, Object message, String title, int optionType, int messageType, Icon icon, Object[] options, Object initialValue) { return CLOSED_OPTION; }
    public static javax.swing.JDialog createDialog(java.awt.Component parentComponent, String title) { return null; }
}
"""

FILES[SW + "UIManager.java"] = """package javax.swing;
/** Minimal javax.swing.UIManager. */
public class UIManager implements java.io.Serializable {
    public static class LookAndFeelInfo implements java.io.Serializable {
        private String name, className;
        public LookAndFeelInfo(String name, String className) { this.name = name; this.className = className; }
        public String getName() { return name; }
        public String getClassName() { return className; }
        public String toString() { return name; }
    }
    private static final java.util.Map<Object, Object> DEFAULTS = new java.util.HashMap<>();
    public static LookAndFeelInfo[] getInstalledLookAndFeels() { return new LookAndFeelInfo[0]; }
    public static void setInstalledLookAndFeels(LookAndFeelInfo[] infos) {}
    public static void installLookAndFeel(LookAndFeelInfo info) {}
    public static void installLookAndFeel(String name, String className) {}
    public static String getSystemLookAndFeelClassName() { return ""; }
    public static String getCrossPlatformLookAndFeelClassName() { return ""; }
    public static Object get(Object key) { return DEFAULTS.get(key); }
    public static Object get(Object key, java.util.Locale l) { return DEFAULTS.get(key); }
    public static void put(Object key, Object value) { DEFAULTS.put(key, value); }
    public static String getString(Object key) { Object v = get(key); return v == null ? null : v.toString(); }
    public static java.awt.Color getColor(Object key) { Object v = get(key); return (v instanceof java.awt.Color) ? (java.awt.Color) v : null; }
    public static java.awt.Font getFont(Object key) { Object v = get(key); return (v instanceof java.awt.Font) ? (java.awt.Font) v : null; }
    public static Icon getIcon(Object key) { Object v = get(key); return (v instanceof Icon) ? (Icon) v : null; }
    public static boolean getBoolean(Object key) { Object v = get(key); return (v instanceof Boolean) && (Boolean) v; }
    public static int getInt(Object key) { Object v = get(key); return (v instanceof Number) ? ((Number) v).intValue() : 0; }
    public static javax.swing.UIDefaults getDefaults() { return null; }
    public static void setLookAndFeel(String className) throws Exception {}
    public static void setLookAndFeel(LookAndFeel newLookAndFeel) {}
    public static LookAndFeel getLookAndFeel() { return null; }
    public static void addPropertyChangeListener(java.beans.PropertyChangeListener listener) {}
    public static void removePropertyChangeListener(java.beans.PropertyChangeListener listener) {}
}
"""

FILES[SW + "LookAndFeel.java"] = """package javax.swing;
/** Minimal javax.swing.LookAndFeel. */
public abstract class LookAndFeel {
    public abstract String getName();
    public abstract String getID();
    public abstract String getDescription();
    public abstract boolean isNativeLookAndFeel();
    public abstract boolean isSupportedLookAndFeel();
    public UIDefaults getDefaults() { return null; }
    public void initialize() {}
    public void uninitialize() {}
    public void provideErrorFeedback(java.awt.Component component) {}
    public String toString() { return getDescription(); }
}
"""

FILES[SW + "UIDefaults.java"] = """package javax.swing;
/** Minimal javax.swing.UIDefaults. */
public class UIDefaults extends java.util.Hashtable<Object, Object> {
    public Object get(Object key) { return super.get(key); }
    public Object put(Object key, Object value) { return super.put(key, value); }
    public void addResourceBundle(String bundleName) {}
    public void removeResourceBundle(String bundleName) {}
}
"""

FILES[SW + "JDialog.java"] = """package javax.swing;
/** Minimal javax.swing.JDialog. */
public class JDialog extends java.awt.Dialog {
    public static final int DISPOSE_ON_CLOSE = 2;
    public static final int DO_NOTHING_ON_CLOSE = 0;
    public static final int HIDE_ON_CLOSE = 1;
    public static final int EXIT_ON_CLOSE = 3;
    private int defaultCloseOperation = HIDE_ON_CLOSE;
    private javax.swing.JMenuBar menuBar;
    private javax.swing.JRootPane rootPane = new javax.swing.JRootPane();
    public JDialog() { super((java.awt.Frame) null); }
    public JDialog(java.awt.Frame owner) { super(owner); }
    public JDialog(java.awt.Frame owner, boolean modal) { super(owner, modal); }
    public JDialog(java.awt.Frame owner, String title) { super(owner, title); }
    public JDialog(java.awt.Frame owner, String title, boolean modal) { super(owner, title, modal); }
    public JDialog(java.awt.Dialog owner) { super(owner); }
    public JDialog(java.awt.Dialog owner, boolean modal) { super(owner); this.modal = modal; }
    public JDialog(java.awt.Dialog owner, String title) { super(owner, title); }
    public JDialog(java.awt.Dialog owner, String title, boolean modal) { super(owner, title); this.modal = modal; }
    public JDialog(java.awt.Frame owner, String title, boolean modal, java.awt.GraphicsConfiguration gc) { super(owner, title, modal); }
    public void setDefaultCloseOperation(int operation) { defaultCloseOperation = operation; }
    public int getDefaultCloseOperation() { return defaultCloseOperation; }
    public javax.swing.JRootPane getRootPane() { return rootPane; }
    public java.awt.Container getContentPane() { return rootPane.getContentPane(); }
    public void setContentPane(java.awt.Container contentPane) { rootPane.setContentPane(contentPane); }
    public void setJMenuBar(javax.swing.JMenuBar menu) { menuBar = menu; }
    public javax.swing.JMenuBar getJMenuBar() { return menuBar; }
    public void setGlassPane(java.awt.Component glass) {}
    public java.awt.Component getGlassPane() { return null; }
    public void setLayeredPane(javax.swing.JLayeredPane layeredPane) {}
    public javax.swing.JLayeredPane getLayeredPane() { return null; }
}
"""

FILES[SW + "JRootPane.java"] = """package javax.swing;
/** Minimal javax.swing.JRootPane. */
public class JRootPane extends JComponent {
    private java.awt.Container contentPane = new javax.swing.JPanel();
    private javax.swing.JLayeredPane layeredPane = new javax.swing.JLayeredPane();
    private java.awt.Component glassPane = new javax.swing.JPanel();
    public java.awt.Container getContentPane() { return contentPane; }
    public void setContentPane(java.awt.Container contentPane) { this.contentPane = contentPane; }
    public javax.swing.JLayeredPane getLayeredPane() { return layeredPane; }
    public void setLayeredPane(javax.swing.JLayeredPane layeredPane) { this.layeredPane = layeredPane; }
    public java.awt.Component getGlassPane() { return glassPane; }
    public void setGlassPane(java.awt.Component glass) { glassPane = glass; }
    public javax.swing.JMenuBar getJMenuBar() { return null; }
    public void setJMenuBar(javax.swing.JMenuBar menu) {}
    public void setWindowDecorationStyle(int windowDecorationStyle) {}
    public int getWindowDecorationStyle() { return 0; }
}
"""

FILES[SW + "JLayeredPane.java"] = """package javax.swing;
/** Minimal javax.swing.JLayeredPane. */
public class JLayeredPane extends JComponent {
    public static final Integer DEFAULT_LAYER = 0;
    public static final Integer PALETTE_LAYER = 100;
    public static final Integer MODAL_LAYER = 200;
    public static final Integer POPUP_LAYER = 300;
    public static final Integer DRAG_LAYER = 400;
    public static final Integer FRAME_CONTENT_LAYER = -30000;
    public void add(java.awt.Component comp, Object constraints) {}
    public void setLayer(java.awt.Component c, int layer) {}
    public int getLayer(java.awt.Component c) { return 0; }
    public void setPosition(java.awt.Component c, int position) {}
    public int getPosition(java.awt.Component c) { return 0; }
}
"""

FILES[SW + "JMenuBar.java"] = """package javax.swing;
/** Minimal javax.swing.JMenuBar. */
public class JMenuBar extends JComponent {
    private final java.util.List<javax.swing.JMenu> menus = new java.util.ArrayList<>();
    public javax.swing.JMenu add(javax.swing.JMenu c) { menus.add(c); return c; }
    public javax.swing.JMenu getMenu(int index) { return menus.get(index); }
    public int getMenuCount() { return menus.size(); }
}
"""

FILES[SW + "JMenu.java"] = """package javax.swing;
/** Minimal javax.swing.JMenu. */
public class JMenu extends JMenuItem {
    private final java.util.List<java.awt.Component> items = new java.util.ArrayList<>();
    public JMenu() {}
    public JMenu(String s) { super(s); }
    public JMenu(String s, boolean b) { super(s); }
    public javax.swing.JMenuItem add(javax.swing.JMenuItem menuItem) { items.add(menuItem); return menuItem; }
    public java.awt.Component add(java.awt.Component c) { items.add(c); return c; }
    public void addSeparator() {}
    public void insert(javax.swing.JMenuItem mi, int pos) { items.add(pos, mi); }
    public void insertSeparator(int index) {}
    public javax.swing.JMenuItem getItem(int pos) { java.awt.Component c = items.get(pos); return (c instanceof javax.swing.JMenuItem) ? (javax.swing.JMenuItem) c : null; }
    public int getItemCount() { return items.size(); }
    public void remove(javax.swing.JMenuItem item) { items.remove(item); }
    public void remove(int pos) { items.remove(pos); }
    public void removeAll() { items.clear(); }
    public boolean isTopLevelMenu() { return false; }
    public boolean isMenuComponent(java.awt.Component c) { return items.contains(c); }
    public void setPopupMenuVisible(boolean b) {}
    public boolean isPopupMenuVisible() { return false; }
    public void setDelay(int d) {}
    public int getDelay() { return 0; }
}
"""

FILES[SW + "border/TitledBorder.java"] = """package javax.swing.border;
import javax.swing.border.Border;
import java.awt.Color;
import java.awt.Font;
/** Minimal javax.swing.border.TitledBorder. */
public class TitledBorder implements Border, java.io.Serializable {
    public static final int DEFAULT_POSITION = 0;
    public static final int ABOVE_TOP = 1;
    public static final int TOP = 2;
    public static final int BELOW_TOP = 3;
    public static final int ABOVE_BOTTOM = 4;
    public static final int BOTTOM = 5;
    public static final int BELOW_BOTTOM = 6;
    public static final int DEFAULT_JUSTIFICATION = 0;
    public static final int LEFT = 1;
    public static final int CENTER = 2;
    public static final int RIGHT = 3;
    public static final int LEADING = 4;
    public static final int TRAILING = 5;
    private Border border;
    private String title;
    private int titleJustification = DEFAULT_JUSTIFICATION;
    private int titlePosition = DEFAULT_POSITION;
    private Font titleFont;
    private Color titleColor;
    public TitledBorder(String title) { this.title = title; }
    public TitledBorder(Border border) { this.border = border; }
    public TitledBorder(Border border, String title) { this.border = border; this.title = title; }
    public TitledBorder(Border border, String title, int titleJustification, int titlePosition) {
        this.border = border; this.title = title; this.titleJustification = titleJustification; this.titlePosition = titlePosition;
    }
    public TitledBorder(Border border, String title, int titleJustification, int titlePosition, Font titleFont) {
        this(border, title, titleJustification, titlePosition); this.titleFont = titleFont;
    }
    public TitledBorder(Border border, String title, int titleJustification, int titlePosition, Font titleFont, Color titleColor) {
        this(border, title, titleJustification, titlePosition, titleFont); this.titleColor = titleColor;
    }
    public void paintBorder(java.awt.Component c, java.awt.Graphics g, int x, int y, int width, int height) {}
    public java.awt.Insets getBorderInsets(java.awt.Component c) { return new java.awt.Insets(0, 0, 0, 0); }
    public boolean isBorderOpaque() { return false; }
    public Border getBorder() { return border; }
    public void setBorder(Border border) { this.border = border; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public int getTitleJustification() { return titleJustification; }
    public void setTitleJustification(int titleJustification) { this.titleJustification = titleJustification; }
    public int getTitlePosition() { return titlePosition; }
    public void setTitlePosition(int titlePosition) { this.titlePosition = titlePosition; }
    public Font getTitleFont() { return titleFont; }
    public void setTitleFont(Font titleFont) { this.titleFont = titleFont; }
    public Color getTitleColor() { return titleColor; }
    public void setTitleColor(Color titleColor) { this.titleColor = titleColor; }
    public java.awt.Dimension getMinimumSize(java.awt.Component c) { return new java.awt.Dimension(0, 0); }
}
"""

FILES[SW + "text/html/HTMLEditorKit.java"] = """package javax.swing.text.html;
import javax.swing.text.*;
/** Minimal javax.swing.text.html.HTMLEditorKit (referenced by ij.gui.HTMLDialog). */
public class HTMLEditorKit extends EditorKit {
    public static final String BOLD_ACTION = "font-bold";
    public static final String ITALIC_ACTION = "font-italic";
    public static final String PARA_INDENT_LEFT = "paragraph-indent-left";
    public static final String PARA_INDENT_RIGHT = "paragraph-indent-right";
    public String getContentType() { return "text/html"; }
    public ViewFactory getViewFactory() { return null; }
    public javax.swing.Action[] getActions() { return new javax.swing.Action[0]; }
    public Caret createCaret() { return null; }
    public Document createDefaultDocument() { return null; }
    public StyleSheet getStyleSheet() { return null; }
    public void setStyleSheet(StyleSheet s) {}
    public void read(java.io.InputStream in, Document doc, int pos) throws java.io.IOException, BadLocationException {}
    public void write(java.io.OutputStream out, Document doc, int pos, int len) throws java.io.IOException, BadLocationException {}
    public void read(java.io.Reader in, Document doc, int pos) throws java.io.IOException, BadLocationException {}
    public void write(java.io.Writer out, Document doc, int pos, int len) throws java.io.IOException, BadLocationException {}
    public void install(javax.swing.text.JTextComponent c) {}
    public void deinstall(javax.swing.text.JTextComponent c) {}
}
"""

FILES[SW + "text/html/StyleSheet.java"] = """package javax.swing.text.html;
import javax.swing.text.Style;
/** Minimal javax.swing.text.html.StyleSheet (referenced by ij.gui.HTMLDialog). */
public class StyleSheet {
    public StyleSheet() {}
    public Style addStyle(String nm, Style parent) { return null; }
    public void removeStyle(String nm) {}
    public Style getStyle(String nm) { return null; }
    public String[] getStyleNames() { return new String[0]; }
    public void addRule(String rule) {}
    public String getRule(String selector) { return null; }
    public void removeRule(String selector) {}
    public void importStyleSheet(java.net.URL url) {}
    public String getDeclaration(String decl) { return null; }
    public void loadRules(java.io.Reader in, java.net.URL ref) {}
    public javax.swing.text.AttributeSet getViewAttributes(javax.swing.text.View v) { return null; }
    public javax.swing.text.AttributeSet translateHTMLToCSS(javax.swing.text.AttributeSet htmlAttrSet) { return null; }
}
"""

FILES[SW + "TransferHandler.java"] = """package javax.swing;
import java.awt.Image;
import java.awt.Point;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.Transferable;
import java.awt.event.InputEvent;
/** Minimal javax.swing.TransferHandler (referenced by ij.io.DragAndDropHandler). */
public class TransferHandler implements java.io.Serializable {
    public static final int NONE = 0;
    public static final int COPY = 1;
    public static final int MOVE = 2;
    public static final int COPY_OR_MOVE = COPY | MOVE;
    public static class TransferSupport {
        private final JComponent component;
        private final Transferable transferable;
        private boolean isDrop;
        private int dropAction = COPY;
        public TransferSupport(JComponent component, Transferable transferable) {
            this.component = component; this.transferable = transferable;
        }
        public JComponent getComponent() { return component; }
        public Transferable getTransferable() { return transferable; }
        public boolean isDrop() { return isDrop; }
        public void setDropAction(int dropAction) { this.dropAction = dropAction; }
        public int getDropAction() { return dropAction; }
        public int getUserDropAction() { return dropAction; }
        public void setShowDropLocation(boolean showDropLocation) {}
        public boolean isShowDropLocation() { return false; }
        public Object getDropLocation() { return null; }
        public java.awt.datatransfer.DataFlavor[] getDataFlavors() { return new java.awt.datatransfer.DataFlavor[0]; }
    }
    public TransferHandler() {}
    public TransferHandler(String property) {}
    public boolean canImport(TransferSupport support) { return false; }
    public boolean importData(TransferSupport support) { return false; }
    public void exportToClipboard(JComponent comp, Clipboard clip, int action) {}
    public void exportAsDrag(JComponent comp, InputEvent e, int action) {}
    public int getSourceActions(JComponent c) { return NONE; }
    public Transferable createTransferable(JComponent c) { return null; }
    public javax.swing.Icon getVisualRepresentation(Transferable t) { return null; }
    public javax.swing.Action getCutAction() { return null; }
    public javax.swing.Action getCopyAction() { return null; }
    public javax.swing.Action getPasteAction() { return null; }
    public Image getDragImage() { return null; }
    public void setDragImage(Image img) {}
    public Point getDragImageOffset() { return new Point(0, 0); }
    public void setDragImageOffset(Point p) {}
}
"""

FILES[SW + "event/ListSelectionListener.java"] = """package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.ListSelectionListener. */
public interface ListSelectionListener extends EventListener {
    void valueChanged(ListSelectionEvent e);
}
"""

FILES[SW + "event/ListSelectionEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.ListSelectionEvent. */
public class ListSelectionEvent extends java.util.EventObject {
    private final int firstIndex, lastIndex;
    private final boolean isAdjusting;
    public ListSelectionEvent(Object source, int firstIndex, int lastIndex, boolean isAdjusting) {
        super(source); this.firstIndex = firstIndex; this.lastIndex = lastIndex; this.isAdjusting = isAdjusting;
    }
    public int getFirstIndex() { return firstIndex; }
    public int getLastIndex() { return lastIndex; }
    public boolean getValueIsAdjusting() { return isAdjusting; }
}
"""

FILES[SW + "event/ListDataListener.java"] = """package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.ListDataListener. */
public interface ListDataListener extends EventListener {
    void intervalAdded(ListDataEvent e);
    void intervalRemoved(ListDataEvent e);
    void contentsChanged(ListDataEvent e);
}
"""

FILES[SW + "event/ListDataEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.ListDataEvent. */
public class ListDataEvent extends java.util.EventObject {
    public static final int CONTENTS_CHANGED = 0;
    public static final int INTERVAL_ADDED = 1;
    public static final int INTERVAL_REMOVED = 2;
    private final int type, index0, index1;
    public ListDataEvent(Object source, int type, int index0, int index1) {
        super(source); this.type = type; this.index0 = index0; this.index1 = index1;
    }
    public int getType() { return type; }
    public int getIndex0() { return index0; }
    public int getIndex1() { return index1; }
}
"""

FILES[SW + "event/TableModelListener.java"] = """package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.TableModelListener. */
public interface TableModelListener extends EventListener {
    void tableChanged(TableModelEvent e);
}
"""

FILES[SW + "event/TableModelEvent.java"] = """package javax.swing.event;
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
"""

FILES[SW + "event/TableColumnModelListener.java"] = """package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.TableColumnModelListener. */
public interface TableColumnModelListener extends EventListener {
    void columnAdded(TableColumnModelEvent e);
    void columnRemoved(TableColumnModelEvent e);
    void columnMoved(TableColumnModelEvent e);
    void columnMarginChanged(javax.swing.event.ChangeEvent e);
    void columnSelectionChanged(ListSelectionEvent e);
}
"""

FILES[SW + "event/TableColumnModelEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.TableColumnModelEvent. */
public class TableColumnModelEvent extends java.util.EventObject {
    private final int fromIndex, toIndex;
    public TableColumnModelEvent(javax.swing.table.TableColumnModel source, int from, int to) {
        super(source); fromIndex = from; toIndex = to;
    }
    public int getFromIndex() { return fromIndex; }
    public int getToIndex() { return toIndex; }
}
"""

FILES[SW + "event/CellEditorListener.java"] = """package javax.swing.event;
import java.util.EventListener;
/** Minimal javax.swing.event.CellEditorListener. */
public interface CellEditorListener extends EventListener {
    void editingStopped(javax.swing.event.ChangeEvent e);
    void editingCanceled(javax.swing.event.ChangeEvent e);
}
"""

FILES[SW + "event/EventListenerList.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.EventListenerList. */
public class EventListenerList implements java.io.Serializable {
    private final java.util.List<Object[]> listeners = new java.util.ArrayList<>();
    public <T extends java.util.EventListener> void add(Class<T> t, T l) { listeners.add(new Object[]{ t, l }); }
    public <T extends java.util.EventListener> void remove(Class<T> t, T l) { listeners.removeIf(e -> e[0] == t && e[1] == l); }
    public <T extends java.util.EventListener> T[] getListeners(Class<T> t) {
        java.util.List<T> out = new java.util.ArrayList<>();
        for (Object[] e : listeners) { if (e[0] == t) out.add(t.cast(e[1])); }
        @SuppressWarnings("unchecked") T[] arr = (T[]) out.toArray(new java.util.EventListener[0]);
        return arr;
    }
    public int getListenerCount() { return listeners.size(); }
    public int getListenerCount(Class<?> t) { int n = 0; for (Object[] e : listeners) { if (e[0] == t) n++; } return n; }
    public Object[] getListenerList() { java.util.List<Object> out = new java.util.ArrayList<>(); for (Object[] e : listeners) { out.add(e[0]); out.add(e[1]); } return out.toArray(); }
}
"""


def main():
    for rel, src in FILES.items():
        path = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print("wrote", rel)
    print(f"{len(FILES)} files")


if __name__ == "__main__":
    main()
