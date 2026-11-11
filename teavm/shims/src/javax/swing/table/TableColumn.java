package javax.swing.table;
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
