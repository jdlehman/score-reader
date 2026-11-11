package javax.swing;
/** Minimal javax.swing.ListCellRenderer. */
public interface ListCellRenderer<E> {
    java.awt.Component getListCellRendererComponent(JList<? extends E> list, E value, int index, boolean isSelected, boolean cellHasFocus);
}
