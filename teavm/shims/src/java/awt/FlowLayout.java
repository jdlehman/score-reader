package java.awt;
/** Minimal java.awt.FlowLayout. */
public class FlowLayout implements LayoutManager, java.io.Serializable {
    public static final int LEFT = 0;
    public static final int CENTER = 1;
    public static final int RIGHT = 2;
    public static final int LEADING = 3;
    public static final int TRAILING = 4;
    protected int align = CENTER, hgap = 5, vgap = 5;
    protected boolean alignOnBaseline;
    public FlowLayout() {}
    public FlowLayout(int align) { this.align = align; }
    public FlowLayout(int align, int hgap, int vgap) { this.align = align; this.hgap = hgap; this.vgap = vgap; }
    public int getAlignment() { return align; }
    public void setAlignment(int align) { this.align = align; }
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
