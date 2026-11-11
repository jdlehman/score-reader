package javax.swing;
import javax.swing.event.ChangeListener;
/** Minimal javax.swing.JScrollBar. */
public class JScrollBar extends JComponent implements java.awt.Adjustable {
    public static final int HORIZONTAL = 0;
    public static final int VERTICAL = 1;
    protected int value, minimum, maximum, visibleAmount, orientation;
    protected int unitIncrement = 1, blockIncrement = 10;
    public JScrollBar() { this(VERTICAL, 0, 10, 0, 100); }
    public JScrollBar(int orientation) { this(orientation, 0, 10, 0, 100); }
    public JScrollBar(int orientation, int value, int visible, int minimum, int maximum) {
        this.orientation = orientation; this.value = value; visibleAmount = visible;
        this.minimum = minimum; this.maximum = maximum;
    }
    public int getOrientation() { return orientation; }
    public void setOrientation(int o) { orientation = o; }
    public int getValue() { return value; }
    public void setValue(int v) { value = v; }
    public int getMinimum() { return minimum; }
    public void setMinimum(int m) { minimum = m; }
    public int getMaximum() { return maximum; }
    public void setMaximum(int m) { maximum = m; }
    public int getVisibleAmount() { return visibleAmount; }
    public void setVisibleAmount(int v) { visibleAmount = v; }
    public int getUnitIncrement() { return unitIncrement; }
    public void setUnitIncrement(int u) { unitIncrement = u; }
    public int getBlockIncrement() { return blockIncrement; }
    public void setBlockIncrement(int b) { blockIncrement = b; }
    public void setValues(int value, int extent, int min, int max) {
        this.value = value; visibleAmount = extent; minimum = min; maximum = max;
    }
    public void addAdjustmentListener(java.awt.event.AdjustmentListener l) {}
    public void removeAdjustmentListener(java.awt.event.AdjustmentListener l) {}
    public java.awt.event.AdjustmentListener[] getAdjustmentListeners() {
        return new java.awt.event.AdjustmentListener[0];
    }
    public void addChangeListener(ChangeListener l) {}
    public void removeChangeListener(ChangeListener l) {}
    public javax.swing.BoundedRangeModel getModel() { return null; }
    public void setModel(javax.swing.BoundedRangeModel model) {}
}
