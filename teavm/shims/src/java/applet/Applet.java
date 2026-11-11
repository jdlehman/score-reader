package java.applet;
import java.awt.Panel;
/** Minimal java.applet.Applet. */
public class Applet extends Panel {
    private AppletStub stub;
    public void init() {}
    public void start() {}
    public void stop() {}
    public void destroy() {}
    public void setStub(AppletStub stub) { this.stub = stub; }
    public AppletStub getStub() { return stub; }
    public boolean isActive() { return false; }
    public java.net.URL getDocumentBase() { return (stub == null) ? null : stub.getDocumentBase(); }
    public java.net.URL getCodeBase() { return (stub == null) ? null : stub.getCodeBase(); }
    public String getParameter(String name) { return (stub == null) ? null : stub.getParameter(name); }
    public AppletContext getAppletContext() { return (stub == null) ? null : stub.getAppletContext(); }
    public void resize(int width, int height) { setSize(width, height); }
    public void resize(java.awt.Dimension d) { setSize(d.width, d.height); }
    public void showStatus(String msg) {}
    public java.awt.Image getImage(java.net.URL url) { return null; }
    public java.awt.Image getImage(java.net.URL url, String name) { return null; }
    public java.applet.AudioClip getAudioClip(java.net.URL url) { return null; }
    public java.applet.AudioClip getAudioClip(java.net.URL url, String name) { return null; }
    public void play(java.net.URL url) {}
    public void play(java.net.URL url, String name) {}
    public String[][] getParameterInfo() { return new String[0][]; }
    public String getAppletInfo() { return ""; }
}
