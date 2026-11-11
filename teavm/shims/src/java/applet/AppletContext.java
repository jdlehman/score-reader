package java.applet;
/** Minimal java.applet.AppletContext. */
public interface AppletContext {
    AudioClip getAudioClip(java.net.URL url);
    java.awt.Image getImage(java.net.URL url);
    Applet getApplet(String name);
    java.util.Enumeration<Applet> getApplets();
    void showDocument(java.net.URL url);
    void showDocument(java.net.URL url, String target);
    void showStatus(String status);
    void setStream(String key, java.io.InputStream stream);
    java.io.InputStream getStream(String key);
    java.util.Iterator<String> getStreamKeys();
}
