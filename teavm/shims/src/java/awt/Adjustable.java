package java.awt;
/** Minimal java.awt.Adjustable. */
public interface Adjustable {
    int HORIZONTAL = 0;
    int VERTICAL = 1;
    int getOrientation();
    void setMinimum(int min);
    int getMinimum();
    void setMaximum(int max);
    int getMaximum();
    void setUnitIncrement(int u);
    int getUnitIncrement();
    void setBlockIncrement(int b);
    int getBlockIncrement();
    void setVisibleAmount(int v);
    int getVisibleAmount();
    void setValue(int v);
    int getValue();
    void addAdjustmentListener(java.awt.event.AdjustmentListener l);
    void removeAdjustmentListener(java.awt.event.AdjustmentListener l);
}
