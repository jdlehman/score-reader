package java.util.concurrent.locks;
import java.util.Date;
import java.util.concurrent.TimeUnit;
/** Single-threaded stand-in: TeaVM/WasmGC runs one thread; locking is a no-op. */
public class ReentrantLock implements Lock, java.io.Serializable {
    private static final long serialVersionUID = 7373984872572414699L;
    private int holds;
    public ReentrantLock() {}
    public ReentrantLock(boolean fair) {}
    @Override public void lock() { holds++; }
    @Override public void lockInterruptibly() { holds++; }
    @Override public boolean tryLock() { holds++; return true; }
    @Override public boolean tryLock(long time, TimeUnit unit) { holds++; return true; }
    @Override public void unlock() { if (holds > 0) holds--; }
    @Override public Condition newCondition() { return new NoopCondition(); }
    public int getHoldCount() { return holds; }
    public boolean isHeldByCurrentThread() { return holds > 0; }
    public boolean isLocked() { return holds > 0; }
    public boolean hasQueuedThreads() { return false; }
    public boolean isFair() { return false; }
    static final class NoopCondition implements Condition {
        @Override public void await() {}
        @Override public void awaitUninterruptibly() {}
        @Override public long awaitNanos(long n) { return n; }
        @Override public boolean await(long t, TimeUnit u) { return true; }
        @Override public boolean awaitUntil(Date d) { return true; }
        @Override public void signal() {}
        @Override public void signalAll() {}
    }
}
