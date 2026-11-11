package java.applet;
/** Minimal java.applet.AppletStub. */
public interface AppletStub {
    boolean isActive();
    java.net.URL getDocumentBase();
    java.net.URL getCodeBase();
    String getParameter(String name);
    AppletContext getAppletContext();
    void appletResize(int width, int height);
}
