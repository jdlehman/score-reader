package javax.swing.event;
import javax.swing.JComponent;
/** Minimal javax.swing.event.AncestorEvent. */
public class AncestorEvent extends java.util.EventObject {
    public static final int ANCESTOR_ADDED = 1;
    public static final int ANCESTOR_REMOVED = 2;
    public static final int ANCESTOR_MOVED = 3;
    protected int id;
    protected JComponent ancestor, ancestorParent;
    public AncestorEvent(JComponent source, int id, JComponent ancestor, JComponent ancestorParent) {
        super(source); this.id = id; this.ancestor = ancestor; this.ancestorParent = ancestorParent;
    }
    public int getID() { return id; }
    public JComponent getAncestor() { return ancestor; }
    public JComponent getAncestorParent() { return ancestorParent; }
    public JComponent getComponent() { return (JComponent) getSource(); }
}
