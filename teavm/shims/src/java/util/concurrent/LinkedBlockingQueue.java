package java.util.concurrent;
import java.util.AbstractQueue;
import java.util.ArrayDeque;
import java.util.Collection;
import java.util.Iterator;
/** Unbounded single-threaded stand-in backed by ArrayDeque. */
public class LinkedBlockingQueue<E> extends AbstractQueue<E> implements BlockingQueue<E> {
    private static final long serialVersionUID = -6903933977591709194L;
    private final ArrayDeque<E> deque = new ArrayDeque<>();
    private final int capacity;
    public LinkedBlockingQueue() { this(Integer.MAX_VALUE); }
    public LinkedBlockingQueue(int capacity) { this.capacity = capacity; }
    public LinkedBlockingQueue(Collection<? extends E> c) { this(Integer.MAX_VALUE); addAll(c); }
    @Override public Iterator<E> iterator() { return deque.iterator(); }
    @Override public int size() { return deque.size(); }
    @Override public boolean offer(E e) { if (deque.size() >= capacity) return false; deque.addLast(e); return true; }
    @Override public E poll() { return deque.pollFirst(); }
    @Override public E peek() { return deque.peekFirst(); }
    @Override public void put(E e) { offer(e); }
    @Override public boolean offer(E e, long t, TimeUnit u) { return offer(e); }
    @Override public E take() { return poll(); }
    @Override public E poll(long t, TimeUnit u) { return poll(); }
    @Override public int remainingCapacity() { return capacity - deque.size(); }
    @Override public int drainTo(Collection<? super E> c) { int n = 0; E e; while ((e = poll()) != null) { c.add(e); n++; } return n; }
    @Override public int drainTo(Collection<? super E> c, int max) { int n = 0; E e; while (n < max && (e = poll()) != null) { c.add(e); n++; } return n; }
}
