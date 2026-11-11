package java.net;
/** Minimal java.net.URLClassLoader. */
public class URLClassLoader extends ClassLoader implements java.io.Closeable {
    private final URL[] urls;
    public URLClassLoader(URL[] urls) { this.urls = (urls == null) ? new URL[0] : urls.clone(); }
    public URLClassLoader(URL[] urls, ClassLoader parent) { super(parent); this.urls = (urls == null) ? new URL[0] : urls.clone(); }
    public static URLClassLoader newInstance(URL[] urls) { return new URLClassLoader(urls); }
    public static URLClassLoader newInstance(URL[] urls, ClassLoader parent) { return new URLClassLoader(urls, parent); }
    public URL[] getURLs() { return urls.clone(); }
    protected void addURL(URL url) {}
    protected Class<?> findClass(String name) throws ClassNotFoundException { throw new ClassNotFoundException(name); }
    public URL findResource(String name) { return null; }
    public java.util.Enumeration<URL> findResources(String name) { return java.util.Collections.emptyEnumeration(); }
    public void close() {}
}
