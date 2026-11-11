package java.awt.geom;
import java.awt.Shape;
/** Minimal java.awt.geom.GeneralPath (extends the Path2D.Float shim). */
public class GeneralPath extends Path2D.Float implements Shape, Cloneable {
    public GeneralPath() { super(); }
    public GeneralPath(int windingRule) { super(windingRule); }
    public GeneralPath(Shape s) { super(); append(s, false); }
    public GeneralPath(int windingRule, int initialCapacity) { super(windingRule); }
    @Override public Object clone() { return super.clone(); }
}
