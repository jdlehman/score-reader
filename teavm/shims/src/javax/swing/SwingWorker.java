package javax.swing;
/** Minimal javax.swing.SwingWorker. */
public abstract class SwingWorker<T, V> implements java.util.concurrent.Future<T>, Runnable {
    public static final int PENDING = 0;
    public static final int STARTED = 1;
    public static final int DONE = 2;
    protected SwingWorker() {}
    protected abstract T doInBackground() throws Exception;
    public final void execute() { run(); }
    public void run() {
        try { doInBackground(); } catch (Exception ignored) {}
        done();
    }
    protected void done() {}
    protected void process(java.util.List<V> chunks) {}
    protected final void publish(V... chunks) {}
    public final T get() throws InterruptedException, java.util.concurrent.ExecutionException { return null; }
    public final T get(long timeout, java.util.concurrent.TimeUnit unit)
            throws InterruptedException, java.util.concurrent.ExecutionException, java.util.concurrent.TimeoutException { return null; }
    public final boolean cancel(boolean mayInterruptIfRunning) { return false; }
    public final boolean isCancelled() { return false; }
    public final boolean isDone() { return true; }
    public final int getState() { return DONE; }
    public final int getProgress() { return 0; }
    protected final void setProgress(int progress) {}
    public final void addPropertyChangeListener(java.beans.PropertyChangeListener l) {}
    public final void removePropertyChangeListener(java.beans.PropertyChangeListener l) {}
    public final void firePropertyChange(String name, Object oldV, Object newV) {}
}
