package java.util.concurrent;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
/** Minimal AbstractExecutorService: submit/invokeAll on top of execute(). */
public abstract class AbstractExecutorService implements ExecutorService {
    @Override public <T> Future<T> submit(Callable<T> task) {
        try { return new ThreadPoolExecutor.DoneFuture<>(task.call()); }
        catch (Throwable e) { return new ThreadPoolExecutor.DoneFuture<>(e); }
    }
    @Override public <T> Future<T> submit(Runnable task, T result) {
        try { task.run(); return new ThreadPoolExecutor.DoneFuture<>(result); }
        catch (Throwable e) { return new ThreadPoolExecutor.DoneFuture<>(e); }
    }
    @Override public Future<?> submit(Runnable task) { return submit(task, null); }
    @Override public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks) {
        List<Future<T>> out = new ArrayList<>();
        for (Callable<T> t : tasks) out.add(submit(t));
        return out;
    }
    @Override public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks, long timeout, TimeUnit unit) {
        return invokeAll(tasks);
    }
    @Override public <T> T invokeAny(Collection<? extends Callable<T>> tasks) throws ExecutionException {
        for (Callable<T> t : tasks) {
            try { return t.call(); } catch (Exception ignored) {}
        }
        throw new ExecutionException("invokeAny: all tasks failed", null);
    }
    @Override public <T> T invokeAny(Collection<? extends Callable<T>> tasks, long timeout, TimeUnit unit)
            throws ExecutionException {
        return invokeAny(tasks);
    }
}
