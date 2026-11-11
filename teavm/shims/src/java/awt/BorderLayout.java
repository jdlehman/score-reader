package java.awt;
/** Minimal java.awt.BorderLayout. */
public class BorderLayout implements LayoutManager2, java.io.Serializable {
    public static final String NORTH = "North";
    public static final String SOUTH = "South";
    public static final String EAST = "East";
    public static final String WEST = "West";
    public static final String CENTER = "Center";
    public static final String BEFORE_FIRST_LINE = "First";
    public static final String AFTER_LAST_LINE = "Last";
    public static final String BEFORE_LINE_BEGINS = "Before";
    public static final String AFTER_LINE_ENDS = "After";
    public static final String PAGE_START = BEFORE_FIRST_LINE;
    public static final String PAGE_END = AFTER_LAST_LINE;
    public static final String LINE_START = BEFORE_LINE_BEGINS;
    public static final String LINE_END = AFTER_LINE_ENDS;
    protected int hgap, vgap;
    public BorderLayout() {}
    public BorderLayout(int hgap, int vgap) { this.hgap = hgap; this.vgap = vgap; }
    public int getHgap() { return hgap; }
    public void setHgap(int hgap) { this.hgap = hgap; }
    public int getVgap() { return vgap; }
    public void setVgap(int vgap) { this.vgap = vgap; }
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
    public String getConstraints(Component comp) { return CENTER; }
}
