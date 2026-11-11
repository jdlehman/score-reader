package java.util.concurrent;
import java.util.AbstractSet;
import java.util.Collection;
import java.util.Comparator;
import java.util.Iterator;
import java.util.Map;
import java.util.NavigableSet;
import java.util.SortedSet;
/** Single-threaded stand-in backed by ConcurrentSkipListMap. */
public class ConcurrentSkipListSet<E> extends AbstractSet<E> implements NavigableSet<E> {
    private static final long serialVersionUID = 1975911028740432611L;
    private final ConcurrentNavigableMap<E, Boolean> map;
    public ConcurrentSkipListSet() { map = new ConcurrentSkipListMap<>(); }
    public ConcurrentSkipListSet(Comparator<? super E> c) { map = new ConcurrentSkipListMap<>(c); }
    public ConcurrentSkipListSet(Collection<? extends E> c) { this(); addAll(c); }
    public ConcurrentSkipListSet(SortedSet<E> s) { this(s.comparator()); addAll(s); }
    @Override public Iterator<E> iterator() { return map.navigableKeySet().iterator(); }
    @Override public int size() { return map.size(); }
    @Override public boolean isEmpty() { return map.isEmpty(); }
    @Override public boolean contains(Object o) { return map.containsKey(o); }
    @Override public boolean add(E e) { return map.putIfAbsent(e, Boolean.TRUE) == null; }
    @Override public boolean remove(Object o) { return map.remove(o, Boolean.TRUE); }
    @Override public void clear() { map.clear(); }
    @Override public Comparator<? super E> comparator() { return map.comparator(); }
    @Override public E first() { return map.firstKey(); }
    @Override public E last() { return map.lastKey(); }
    @Override public E lower(E e) { return map.lowerKey(e); }
    @Override public E floor(E e) { return map.floorKey(e); }
    @Override public E ceiling(E e) { return map.ceilingKey(e); }
    @Override public E higher(E e) { return map.higherKey(e); }
    @Override public E pollFirst() { Map.Entry<E, Boolean> e = map.pollFirstEntry(); return e == null ? null : e.getKey(); }
    @Override public E pollLast() { Map.Entry<E, Boolean> e = map.pollLastEntry(); return e == null ? null : e.getKey(); }
    @Override public NavigableSet<E> descendingSet() { throw new UnsupportedOperationException(); }
    @Override public Iterator<E> descendingIterator() { return map.descendingKeySet().iterator(); }
    @Override public NavigableSet<E> subSet(E a, boolean ai, E b, boolean bi) { throw new UnsupportedOperationException(); }
    @Override public NavigableSet<E> headSet(E to, boolean incl) { throw new UnsupportedOperationException(); }
    @Override public NavigableSet<E> tailSet(E from, boolean incl) { throw new UnsupportedOperationException(); }
    @Override public SortedSet<E> subSet(E a, E b) { throw new UnsupportedOperationException(); }
    @Override public SortedSet<E> headSet(E to) { throw new UnsupportedOperationException(); }
    @Override public SortedSet<E> tailSet(E from) { throw new UnsupportedOperationException(); }
}
