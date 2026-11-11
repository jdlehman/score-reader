package javax.swing;
/** Minimal javax.swing.DefaultListModel. */
public class DefaultListModel<E> extends AbstractListModel<E> {
    private final java.util.List<E> delegate = new java.util.ArrayList<>();
    public int getSize() { return delegate.size(); }
    public E getElementAt(int index) { return delegate.get(index); }
    public void addElement(E element) { delegate.add(element); fireIntervalAdded(this, delegate.size() - 1, delegate.size() - 1); }
    public void insertElementAt(E element, int index) { delegate.add(index, element); fireIntervalAdded(this, index, index); }
    public boolean removeElement(Object obj) { int i = delegate.indexOf(obj); if (i < 0) return false; delegate.remove(i); fireIntervalRemoved(this, i, i); return true; }
    public void removeElementAt(int index) { delegate.remove(index); fireIntervalRemoved(this, index, index); }
    public void removeAllElements() { int n = delegate.size(); delegate.clear(); if (n > 0) fireIntervalRemoved(this, 0, n - 1); }
    public void clear() { removeAllElements(); }
    public void add(int index, E element) { insertElementAt(element, index); }
    public E remove(int index) { E e = delegate.remove(index); fireIntervalRemoved(this, index, index); return e; }
    public boolean remove(Object o) { return removeElement(o); }
    public E get(int index) { return delegate.get(index); }
    public E set(int index, E element) { E old = delegate.set(index, element); fireContentsChanged(this, index, index); return old; }
    public void setElementAt(E element, int index) { set(index, element); }
    public boolean contains(Object elem) { return delegate.contains(elem); }
    public int indexOf(Object elem) { return delegate.indexOf(elem); }
    public int indexOf(Object elem, int index) { return delegate.indexOf(elem); }
    public int lastIndexOf(Object elem) { return delegate.lastIndexOf(elem); }
    public E firstElement() { return delegate.get(0); }
    public E lastElement() { return delegate.get(delegate.size() - 1); }
    public boolean isEmpty() { return delegate.isEmpty(); }
    public int size() { return delegate.size(); }
    public Object[] toArray() { return delegate.toArray(); }
    public <T> T[] toArray(T[] a) { return delegate.toArray(a); }
    public java.util.Enumeration<E> elements() { return java.util.Collections.enumeration(delegate); }
    public void copyInto(Object[] anArray) { delegate.toArray(anArray); }
    public void setSize(int newSize) { while (delegate.size() > newSize) delegate.remove(delegate.size() - 1); while (delegate.size() < newSize) delegate.add(null); }
    public void trimToSize() {}
    public void ensureCapacity(int minCapacity) {}
}
