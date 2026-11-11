package java.util.concurrent;
import java.util.AbstractQueue;
import java.util.Collection;
import java.util.Iterator;
import java.util.concurrent.TimeUnit;
/** Minimal java.util.concurrent.SynchronousQueue.
 *  Stub semantics: backed by a plain queue (no handoff); never used at
 *  runtime in the TeaVM demo, only needed so ij.util.ThreadUtil compiles. */
public class SynchronousQueue<E> extends AbstractQueue<E> implements BlockingQueue<E>, java.io.Serializable {
    private final java.util.Queue<E> delegate = new java.util.ArrayDeque<>();
    public SynchronousQueue() {}
    public SynchronousQueue(boolean fair) {}
    public boolean offer(E e) { return delegate.offer(e); }
    public E poll() { return delegate.poll(); }
    public E peek() { return delegate.peek(); }
    public Iterator<E> iterator() { return delegate.iterator(); }
    public int size() { return delegate.size(); }
    public void put(E e) { delegate.offer(e); }
    public boolean offer(E e, long timeout, TimeUnit unit) { return offer(e); }
    public E take() { return delegate.poll(); }
    public E poll(long timeout, TimeUnit unit) { return delegate.poll(); }
    public int remainingCapacity() { return 0; }
    public int drainTo(Collection<? super E> c) { int n = 0; E e; while ((e = delegate.poll()) != null) { c.add(e); n++; } return n; }
    public int drainTo(Collection<? super E> c, int maxElements) { int n = 0; E e; while (n < maxElements && (e = delegate.poll()) != null) { c.add(e); n++; } return n; }
    public boolean contains(Object o) { return delegate.contains(o); }
    public Object[] toArray() { return delegate.toArray(); }
    public <T> T[] toArray(T[] a) { return delegate.toArray(a); }
    public boolean remove(Object o) { return delegate.remove(o); }
    public void clear() { delegate.clear(); }
}
