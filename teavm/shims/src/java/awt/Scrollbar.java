package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Scrollbar. */
public class Scrollbar extends Component implements Adjustable {
    public static final int HORIZONTAL = 0;
    public static final int VERTICAL = 1;
    protected int value, minimum, maximum, visibleAmount, orientation;
    protected int unitIncrement = 1, blockIncrement = 10;
    public Scrollbar() { this(VERTICAL, 0, 10, 0, 100); }
    public Scrollbar(int orientation) { this(orientation, 0, 10, 0, 100); }
    public Scrollbar(int orientation, int value, int visible, int minimum, int maximum) {
        this.orientation = orientation; this.value = value; this.visibleAmount = visible;
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
    public void addAdjustmentListener(AdjustmentListener l) {}
    public void removeAdjustmentListener(AdjustmentListener l) {}
    public AdjustmentListener[] getAdjustmentListeners() { return new AdjustmentListener[0]; }
    public void setValues(int value, int visible, int minimum, int maximum) {
        this.value = value; visibleAmount = visible; this.minimum = minimum; this.maximum = maximum;
    }
}
