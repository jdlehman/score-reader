package java.util.concurrent;
import java.util.AbstractCollection;
import java.util.AbstractSet;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.Iterator;
import java.util.Map;
import java.util.NavigableMap;
import java.util.NavigableSet;
import java.util.NoSuchElementException;
import java.util.Set;
import java.util.SortedMap;
import java.util.SortedSet;
import java.util.TreeMap;
/**
 * Single-threaded stand-in backed by TreeMap.
 *
 * TEAVM: TreeMap's iterators are fail-fast, but the JDK contract for
 * ConcurrentSkipListMap/Set is weakly consistent: iteration must tolerate
 * re-entrant modification (Audiveris UnitManager.checkDirtySets() iterates
 * dirtySets while initialize() re-entrantly registers another ConstantSet).
 * The collection views below therefore iterate over a snapshot taken at
 * iterator() time; iterator.remove() still removes from the live map.
 * New keys added during iteration are not visited (as with a weakly
 * consistent iterator); removed keys are still visited if snapshotted.
 */
public class ConcurrentSkipListMap<K, V> extends TreeMap<K, V> implements ConcurrentNavigableMap<K, V> {
    private static final long serialVersionUID = 1975911028740432610L;
    public ConcurrentSkipListMap() { super(); }
    public ConcurrentSkipListMap(Comparator<? super K> c) { super(c); }
    public ConcurrentSkipListMap(Map<? extends K, ? extends V> m) { super(m); }
    public ConcurrentSkipListMap(SortedMap<K, ? extends V> m) { super(m); }
    @Override public V putIfAbsent(K k, V v) { V old = get(k); if (old == null) put(k, v); return old; }
    @Override public boolean remove(Object k, Object v) { if (v != null && v.equals(get(k))) { remove(k); return true; } return false; }
    @Override public boolean replace(K k, V oldV, V newV) { if (oldV != null && oldV.equals(get(k))) { put(k, newV); return true; } return false; }
    @Override public V replace(K k, V v) { return containsKey(k) ? put(k, v) : null; }
    @Override public ConcurrentNavigableMap<K, V> subMap(K a, boolean ai, K b, boolean bi) { return new ConcurrentSkipListMap<>(super.subMap(a, ai, b, bi)); }
    @Override public ConcurrentNavigableMap<K, V> headMap(K to, boolean incl) { return new ConcurrentSkipListMap<>(super.headMap(to, incl)); }
    @Override public ConcurrentNavigableMap<K, V> tailMap(K from, boolean incl) { return new ConcurrentSkipListMap<>(super.tailMap(from, incl)); }
    @Override public ConcurrentNavigableMap<K, V> subMap(K a, K b) { return new ConcurrentSkipListMap<>(super.subMap(a, b)); }
    @Override public ConcurrentNavigableMap<K, V> headMap(K to) { return new ConcurrentSkipListMap<>(super.headMap(to)); }
    @Override public ConcurrentNavigableMap<K, V> tailMap(K from) { return new ConcurrentSkipListMap<>(super.tailMap(from)); }
    @Override public ConcurrentNavigableMap<K, V> descendingMap() { return new ConcurrentSkipListMap<>(super.descendingMap()); }
    @Override public NavigableSet<K> navigableKeySet() { return new SnapNavSet<>(super.navigableKeySet(), this); }
    @Override public NavigableSet<K> descendingKeySet() { return new SnapNavSet<>(super.descendingKeySet(), this); }
    @Override public Set<Map.Entry<K, V>> entrySet() { return new SnapSet<>(super.entrySet(), this); }
    @Override public Collection<V> values() { return new SnapCollection<>(super.values(), this); }
    @Override public Set<K> keySet() { return new SnapSet<>(super.keySet(), this); }

    /** Iterator over a snapshot; remove() removes from the live map. */
    private static final class SnapIterator<E> implements Iterator<E> {
        private final Iterator<E> it;
        private final Map<?, ?> live;
        private E last;
        SnapIterator(Collection<E> snapshot, Map<?, ?> live) {
            this.it = new ArrayList<>(snapshot).iterator();
            this.live = live;
        }
        @Override public boolean hasNext() { return it.hasNext(); }
        @Override public E next() { last = it.next(); return last; }
        @Override public void remove() {
            if (last == null) throw new IllegalStateException();
            // Entry snapshots carry their key in the entry itself.
            Object key = (last instanceof Map.Entry) ? ((Map.Entry<?, ?>) last).getKey() : last;
            live.remove(key);
            last = null;
        }
    }

    /** Snapshot-iterating set view; reads delegate to the live view. */
    private static final class SnapSet<E> extends AbstractSet<E> {
        private final Set<E> live;
        private final Map<?, ?> map;
        SnapSet(Set<E> live, Map<?, ?> map) { this.live = live; this.map = map; }
        @Override public Iterator<E> iterator() { return new SnapIterator<>(live, map); }
        @Override public int size() { return live.size(); }
        @Override public boolean contains(Object o) { return live.contains(o); }
        @Override public boolean remove(Object o) { return live.remove(o); }
    }

    private static final class SnapCollection<E> extends AbstractCollection<E> {
        private final Collection<E> live;
        private final Map<?, ?> map;
        SnapCollection(Collection<E> live, Map<?, ?> map) { this.live = live; this.map = map; }
        @Override public Iterator<E> iterator() { return new SnapValueIterator<>(live, map); }
        @Override public int size() { return live.size(); }
        @Override public boolean contains(Object o) { return live.contains(o); }
    }

    /** Values iterator: snapshots entries, removes by entry key. */
    private static final class SnapValueIterator<K, V> implements Iterator<V> {
        private final Iterator<Map.Entry<K, V>> it;
        private final Map<K, V> live;
        private Map.Entry<K, V> last;
        @SuppressWarnings("unchecked")
        SnapValueIterator(Collection<V> values, Map<?, ?> live) {
            // values() came from this map's entry set; rebuild entry snapshot.
            this.it = new ArrayList<>(((ConcurrentSkipListMap<K, V>) live).entrySet()).iterator();
            this.live = (Map<K, V>) live;
        }
        @Override public boolean hasNext() { return it.hasNext(); }
        @Override public V next() { last = it.next(); return last.getValue(); }
        @Override public void remove() {
            if (last == null) throw new IllegalStateException();
            live.remove(last.getKey());
            last = null;
        }
    }

    /** Snapshot-iterating navigable set view; navigation delegates live. */
    private static final class SnapNavSet<K> extends AbstractSet<K> implements NavigableSet<K> {
        private final NavigableSet<K> live;
        private final Map<?, ?> map;
        SnapNavSet(NavigableSet<K> live, Map<?, ?> map) { this.live = live; this.map = map; }
        @Override public Iterator<K> iterator() { return new SnapIterator<>(live, map); }
        @Override public int size() { return live.size(); }
        @Override public boolean contains(Object o) { return live.contains(o); }
        @Override public boolean remove(Object o) { return live.remove(o); }
        @Override public Comparator<? super K> comparator() { return live.comparator(); }
        @Override public K first() { return live.first(); }
        @Override public K last() { return live.last(); }
        @Override public K lower(K e) { return live.lower(e); }
        @Override public K floor(K e) { return live.floor(e); }
        @Override public K ceiling(K e) { return live.ceiling(e); }
        @Override public K higher(K e) { return live.higher(e); }
        @Override public K pollFirst() { return live.pollFirst(); }
        @Override public K pollLast() { return live.pollLast(); }
        @Override public Iterator<K> descendingIterator() { return new SnapIterator<>(live.descendingSet(), map); }
        @Override public NavigableSet<K> descendingSet() { return new SnapNavSet<>(live.descendingSet(), map); }
        @Override public NavigableSet<K> subSet(K a, boolean ai, K b, boolean bi) { return new SnapNavSet<>(live.subSet(a, ai, b, bi), map); }
        @Override public NavigableSet<K> headSet(K to, boolean incl) { return new SnapNavSet<>(live.headSet(to, incl), map); }
        @Override public NavigableSet<K> tailSet(K from, boolean incl) { return new SnapNavSet<>(live.tailSet(from, incl), map); }
        @Override public SortedSet<K> subSet(K a, K b) { return subSet(a, true, b, false); }
        @Override public SortedSet<K> headSet(K to) { return headSet(to, false); }
        @Override public SortedSet<K> tailSet(K from) { return tailSet(from, true); }
    }
}
