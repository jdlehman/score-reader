package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JSplitPane. */
public class JSplitPane extends JComponent {
    public static final int VERTICAL_SPLIT = 0;
    public static final int HORIZONTAL_SPLIT = 1;
    protected Component left, right;
    protected int orientation = HORIZONTAL_SPLIT;
    protected int dividerLocation = -1;
    protected int dividerSize = 10;
    public JSplitPane() {}
    public JSplitPane(int orientation) { this.orientation = orientation; }
    public JSplitPane(int orientation, Component left, Component right) {
        this.orientation = orientation; this.left = left; this.right = right;
    }
    public JSplitPane(int orientation, boolean continuousLayout, Component left, Component right) {
        this.orientation = orientation; this.left = left; this.right = right;
    }
    public void setLeftComponent(Component c) { left = c; }
    public Component getLeftComponent() { return left; }
    public void setRightComponent(Component c) { right = c; }
    public Component getRightComponent() { return right; }
    public void setTopComponent(Component c) { left = c; }
    public Component getTopComponent() { return left; }
    public void setBottomComponent(Component c) { right = c; }
    public Component getBottomComponent() { return right; }
    public int getOrientation() { return orientation; }
    public void setOrientation(int o) { orientation = o; }
    public int getDividerLocation() { return dividerLocation; }
    public void setDividerLocation(int loc) { dividerLocation = loc; }
    public void setDividerLocation(double proportional) {}
    public int getDividerSize() { return dividerSize; }
    public void setDividerSize(int size) { dividerSize = size; }
    public void setOneTouchExpandable(boolean b) {}
    public boolean isOneTouchExpandable() { return false; }
    public void setResizeWeight(double w) {}
    public double getResizeWeight() { return 0; }
    public void setContinuousLayout(boolean b) {}
    public boolean isContinuousLayout() { return false; }
    public void setLastDividerLocation(int loc) {}
    public int getLastDividerLocation() { return -1; }
    public void resetToPreferredSizes() {}
}
