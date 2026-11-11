package java.awt;
/** Minimal java.awt.GridBagLayout. */
public class GridBagLayout implements LayoutManager2, java.io.Serializable {
    protected GridBagConstraints defaultConstraints = new GridBagConstraints();
    public GridBagLayout() {}
    public void addLayoutComponent(Component comp, Object constraints) {}
    public void addLayoutComponent(String name, Component comp) {}
    public void removeLayoutComponent(Component comp) {}
    public Dimension preferredLayoutSize(Container parent) { return new Dimension(0, 0); }
    public Dimension minimumLayoutSize(Container parent) { return new Dimension(0, 0); }
    public Dimension maximumLayoutSize(Container target) { return new Dimension(Integer.MAX_VALUE, Integer.MAX_VALUE); }
    public float getLayoutAlignmentX(Container target) { return 0.5f; }
    public float getLayoutAlignmentY(Container target) { return 0.5f; }
    public void invalidateLayout(Container target) {}
    public void layoutContainer(Container parent) {}
    public GridBagConstraints getConstraints(Component comp) { return new GridBagConstraints(); }
    public void setConstraints(Component comp, GridBagConstraints constraints) {}
    protected GridBagConstraints lookupConstraints(Component comp) { return new GridBagConstraints(); }
    public java.awt.Point getLayoutOrigin() { return new java.awt.Point(0, 0); }
    public int[][] getLayoutDimensions() { return new int[2][0]; }
    public double[][] getLayoutWeights() { return new double[2][0]; }
    public java.awt.Point location(int x, int y) { return new java.awt.Point(0, 0); }
}
