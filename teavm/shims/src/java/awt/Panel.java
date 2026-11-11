package java.awt;
/** Minimal java.awt.Panel. */
public class Panel extends Container {
    public Panel() {}
    public Panel(LayoutManager layout) { setLayout(layout); }
}
