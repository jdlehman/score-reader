package javax.swing;
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
