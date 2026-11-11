package java.util.concurrent;
/** Factories returning the inline executor (ThreadFactory ignored: no real threads). */
public final class Executors {
    private Executors() {}
    public static ExecutorService newFixedThreadPool(int nThreads) {
        return new ThreadPoolExecutor(nThreads, nThreads, 0L, TimeUnit.MILLISECONDS, new LinkedBlockingQueue<>());
    }
    public static ExecutorService newFixedThreadPool(int nThreads, ThreadFactory f) {
        return newFixedThreadPool(nThreads);
    }
    public static ExecutorService newCachedThreadPool() {
        return new ThreadPoolExecutor(0, Integer.MAX_VALUE, 60L, TimeUnit.SECONDS, new LinkedBlockingQueue<>());
    }
    public static ExecutorService newCachedThreadPool(ThreadFactory f) { return newCachedThreadPool(); }
    public static ExecutorService newSingleThreadExecutor() { return newFixedThreadPool(1); }
    public static ExecutorService newSingleThreadExecutor(ThreadFactory f) { return newFixedThreadPool(1); }
    public static ExecutorService newWorkStealingPool() { return newCachedThreadPool(); }
    public static ExecutorService newWorkStealingPool(int p) { return newCachedThreadPool(); }
    public static ExecutorService newScheduledThreadPool(int core) { return newFixedThreadPool(core); }
    public static ExecutorService newScheduledThreadPool(int core, ThreadFactory f) { return newFixedThreadPool(core); }
    public static ExecutorService unconfigurableExecutorService(ExecutorService e) { return e; }
    public static Callable<Object> callable(Runnable task) { return () -> { task.run(); return null; }; }
    public static <T> Callable<T> callable(Runnable task, T result) { return () -> { task.run(); return result; }; }
}
