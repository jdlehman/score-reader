package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetContext. */
public class DropTargetContext implements java.io.Serializable {
    public DropTarget getDropTarget() { return null; }
    public java.awt.Component getComponent() { return null; }
    public void addNotify(java.awt.peer.DropTargetPeer dtp) {}
    public void removeNotify() {}
    protected void setDropTargetContextPeer(java.awt.peer.DropTargetPeer dtp) {}
}
