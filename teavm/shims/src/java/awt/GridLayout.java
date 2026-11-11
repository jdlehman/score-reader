package java.awt;
/** Minimal java.awt.GridLayout. */
public class GridLayout implements LayoutManager, java.io.Serializable {
    protected int rows, cols, hgap, vgap;
    public GridLayout() { this(1, 0, 0, 0); }
    public GridLayout(int rows, int cols) { this(rows, cols, 0, 0); }
    public GridLayout(int rows, int cols, int hgap, int vgap) {
        this.rows = rows; this.cols = cols; this.hgap = hgap; this.vgap = vgap;
    }
    public int getRows() { return rows; }
    public void setRows(int rows) { this.rows = rows; }
    public int getColumns() { return cols; }
    public void setColumns(int cols) { this.cols = cols; }
    public int getHgap() { return hgap; }
    public void setHgap(int hgap) { this.hgap = hgap; }
    public int getVgap() { return vgap; }
    public void setVgap(int vgap) { this.vgap = vgap; }
    public void addLayoutComponent(String name, Component comp) {}
    public void removeLayoutComponent(Component comp) {}
    public Dimension preferredLayoutSize(Container parent) { return new Dimension(0, 0); }
    public Dimension minimumLayoutSize(Container parent) { return new Dimension(0, 0); }
    public void layoutContainer(Container parent) {}
}
