package java.lang;
/** Minimal java.lang.Process (analysis stub). */
public abstract class Process {
    public Process() {}
    public abstract java.io.OutputStream getOutputStream();
    public abstract java.io.InputStream getInputStream();
    public abstract java.io.InputStream getErrorStream();
    public abstract int waitFor() throws InterruptedException;
    public abstract int exitValue();
    public abstract void destroy();
    public boolean isAlive() { return false; }
    public Process destroyForcibly() { destroy(); return this; }
    public boolean waitFor(long timeout, java.util.concurrent.TimeUnit unit) throws InterruptedException { return true; }
}
