package java.util.concurrent;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
/** Inline executor: runs every task on the submitting thread, immediately.
 *  Correct for Audiveris's fork-join style use (submit then get); no parallelism. */
public class ThreadPoolExecutor extends AbstractExecutorService {
    private volatile boolean shutdown;
    public ThreadPoolExecutor(int corePoolSize, int maximumPoolSize, long keepAliveTime,
                              TimeUnit unit, BlockingQueue<Runnable> workQueue) {}
    public ThreadPoolExecutor(int corePoolSize, int maximumPoolSize, long keepAliveTime,
                              TimeUnit unit, BlockingQueue<Runnable> workQueue, ThreadFactory f) {}
    public ThreadPoolExecutor(int corePoolSize, int maximumPoolSize, long keepAliveTime,
                              TimeUnit unit, BlockingQueue<Runnable> workQueue,
                              RejectedExecutionHandler h) {}
    public ThreadPoolExecutor(int corePoolSize, int maximumPoolSize, long keepAliveTime,
                              TimeUnit unit, BlockingQueue<Runnable> workQueue,
                              ThreadFactory f, RejectedExecutionHandler h) {}
    @Override public void execute(Runnable command) { command.run(); }
    public void purge() {}
    @Override public void shutdown() { shutdown = true; }
    @Override public List<Runnable> shutdownNow() { shutdown = true; return new ArrayList<>(); }
    @Override public boolean isShutdown() { return shutdown; }
    @Override public boolean isTerminated() { return shutdown; }
    @Override public boolean awaitTermination(long timeout, TimeUnit unit) { return true; }
    static final class DoneFuture<V> implements Future<V> {
        private final V value; private final Throwable error;
        DoneFuture(V v) { value = v; error = null; }
        DoneFuture(Throwable e) { value = null; error = e; }
        @Override public boolean cancel(boolean b) { return false; }
        @Override public boolean isCancelled() { return false; }
        @Override public boolean isDone() { return true; }
        @Override public V get() throws ExecutionException {
            if (error != null) throw new ExecutionException(error);
            return value;
        }
        @Override public V get(long t, TimeUnit u) throws ExecutionException { return get(); }
    }
}
