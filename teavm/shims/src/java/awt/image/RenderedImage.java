package java.awt.image;
import java.awt.Rectangle;
public interface RenderedImage {
    java.util.Vector<RenderedImage> getSources();
    Object getProperty(String name);
    String[] getPropertyNames();
    ColorModel getColorModel();
    SampleModel getSampleModel();
    int getWidth();
    int getHeight();
    int getMinX();
    int getMinY();
    int getNumXTiles();
    int getNumYTiles();
    int getMinTileX();
    int getMinTileY();
    int getTileWidth();
    int getTileHeight();
    int getTileGridXOffset();
    int getTileGridYOffset();
    Raster getTile(int tileX, int tileY);
    Raster getData();
    Raster getData(Rectangle rect);
    WritableRaster copyData(WritableRaster raster);
}
