package java.awt;
/** Minimal java.awt.Insets. */
public class Insets implements Cloneable {
    public int top, left, bottom, right;
    public Insets(int top, int left, int bottom, int right) {
        this.top = top; this.left = left; this.bottom = bottom; this.right = right;
    }
    @Override public boolean equals(Object o) {
        if (o instanceof Insets i) return top == i.top && left == i.left && bottom == i.bottom && right == i.right;
        return false;
    }
    @Override public int hashCode() { return top * 31 * 31 * 31 + left * 31 * 31 + bottom * 31 + right; }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
    @Override public String toString() { return "Insets[" + top + "," + left + "," + bottom + "," + right + "]"; }
}
