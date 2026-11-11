package teavm;

import java.awt.image.BufferedImage;

/** Static holder for the JS-supplied grey image (patched LoadStep reads it). */
public class TeavmImageHolder
{
    public static BufferedImage image;

    public static BufferedImage getImage ()
    {
        return image;
    }
}
