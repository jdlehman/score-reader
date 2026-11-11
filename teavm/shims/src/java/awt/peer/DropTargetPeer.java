package java.awt.peer;
/** Minimal java.awt.peer.DropTargetPeer. */
public interface DropTargetPeer {
    void addDropTarget(java.awt.dnd.DropTarget dt);
    void removeDropTarget(java.awt.dnd.DropTarget dt);
}
