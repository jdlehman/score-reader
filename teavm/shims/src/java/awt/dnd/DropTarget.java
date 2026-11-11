package java.awt.dnd;
/** Minimal java.awt.dnd.DropTarget. */
public class DropTarget implements java.io.Serializable {
    public DropTarget() {}
    public DropTarget(java.awt.Component comp, DropTargetListener dtl) {}
    public DropTarget(java.awt.Component comp, int ops, DropTargetListener dtl) {}
    public DropTarget(java.awt.Component comp, int ops, DropTargetListener dtl, boolean active) {}
    public DropTarget(java.awt.Component comp, int ops, DropTargetListener dtl, boolean active, java.awt.datatransfer.FlavorMap fm) {}
    public void setComponent(java.awt.Component comp) {}
    public java.awt.Component getComponent() { return null; }
    public void setDefaultActions(int ops) {}
    public int getDefaultActions() { return 0; }
    public void setActive(boolean isActive) {}
    public boolean isActive() { return false; }
    public void addDropTargetListener(DropTargetListener dtl) {}
    public void removeDropTargetListener(DropTargetListener dtl) {}
}
