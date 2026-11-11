package javax.swing.event;
/** Minimal javax.swing.event.PopupMenuListener. */
public interface PopupMenuListener extends java.util.EventListener {
    void popupMenuWillBecomeVisible(PopupMenuEvent e);
    void popupMenuWillBecomeInvisible(PopupMenuEvent e);
    void popupMenuCanceled(PopupMenuEvent e);
}
