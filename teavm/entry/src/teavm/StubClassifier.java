package teavm;

import java.util.Collection;
import java.util.EnumSet;

import org.audiveris.omr.classifier.Classifier;
import org.audiveris.omr.classifier.Evaluation;
import org.audiveris.omr.classifier.GlyphDescriptor;
import org.audiveris.omr.classifier.Sample;
import org.audiveris.omr.classifier.TrainingMonitor;
import org.audiveris.omr.glyph.Glyph;
import org.audiveris.omr.sheet.SystemInfo;

/**
 * TEAVM Phase-A stub classifier: the neural model (zip + ZipFS + JAXB) cannot
 * load in WASM, so every evaluation returns empty. Steps still run; they just
 * find no classified shapes (clefs, keys, times, symbols).
 */
public class StubClassifier
        implements Classifier
{
    public static final StubClassifier INSTANCE = new StubClassifier();

    private StubClassifier ()
    {
    }

    @Override
    public void addListener (TrainingMonitor listener)
    {
    }

    @Override
    public Evaluation[] evaluate (Glyph glyph,
                                  int interline,
                                  int count,
                                  double minGrade,
                                  EnumSet<Classifier.Condition> conditions)
    {
        return new Evaluation[0];
    }

    @Override
    public Evaluation[] evaluate (Glyph glyph,
                                  SystemInfo system,
                                  int count,
                                  double minGrade,
                                  EnumSet<Classifier.Condition> conditions)
    {
        return new Evaluation[0];
    }

    @Override
    public int getEpochsTotal ()
    {
        return 0;
    }

    @Override
    public GlyphDescriptor getGlyphDescriptor ()
    {
        return null;
    }

    @Override
    public double getLambda ()
    {
        return 0;
    }

    @Override
    public double getLearningRate ()
    {
        return 0;
    }

    @Override
    public int getMaxEpochs ()
    {
        return 0;
    }

    @Override
    public double getMomentum ()
    {
        return 0;
    }

    @Override
    public String getName ()
    {
        return "stub";
    }

    @Override
    public Evaluation[] getNaturalEvaluations (Glyph glyph,
                                               int interline)
    {
        return new Evaluation[0];
    }

    @Override
    public boolean isBigEnough (Glyph glyph,
                                int interline)
    {
        return false;
    }

    @Override
    public boolean isBigEnough (double weight)
    {
        return false;
    }

    @Override
    public void reset ()
    {
    }

    @Override
    public void setLambda (double lambda)
    {
    }

    @Override
    public void setLearningRate (double learningRate)
    {
    }

    @Override
    public void setMomentum (double momentum)
    {
    }

    @Override
    public void stop ()
    {
    }

    @Override
    public void train (Collection<Sample> samples,
                       int epochs)
    {
    }
}
