package java.lang.ref;
/**
 * Minimal java.lang.ref.PhantomReference.
 * Mirrors TeaVM's TWeakReference: stores the referent in a field because
 * TeaVM's TReference has only a no-arg constructor (no (Object) or
 * (Object, ReferenceQueue) ctor). The super(referent) call below is for
 * javac (JDK Reference has no no-arg ctor); the build rewrites it to
 * super() in the class file fed to TeaVM (see tools/rewrite_jars).
 */
public final class PhantomReference<T> extends Reference<T> {
    private T value;

    public PhantomReference(T referent, ReferenceQueue<? super T> q) {
        super(referent);
        value = referent;
    }

    @Override
    public T get() {
        return value;
    }

    @Override
    public void clear() {
        value = null;
    }

    @Override
    public boolean isEnqueued() {
        return false;
    }

    @Override
    public boolean enqueue() {
        return false;
    }
}
