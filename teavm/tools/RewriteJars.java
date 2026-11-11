import org.objectweb.asm.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import java.util.zip.*;

/**
 * ASM jar rewriter for the TeaVM spike.
 *
 * Modes:
 *   ij <in.jar> <out.jar>
 *     Rewrite GETSTATIC java/awt/Color.<lowercase> field refs to TColor
 *     equivalents (TeaVM's classlib TColor has only BLACK and WHITE).
 *     Exact: black->BLACK, white->WHITE. GUI-only approximations (documented):
 *     lightGray/gray->WHITE, darkGray/red/green/blue/yellow/magenta/cyan/
 *     orange/pink->BLACK. Prints a full report of every java/awt/Color
 *     member reference found (fields AND methods) so getRGB/decode-style
 *     gaps are visible instead of silently missed.
 *     Also fixes the requestFocus ()V -> ()Z mismatch (ij was compiled
 *     against a Component.requestFocus()V) and neuters the IJ_NEUTER
 *     methods below, whose bodies call classlib-missing members
 *     (Color.getRGB, ClassLoader.*, System.*, Runtime.*, Thread.*) in
 *     ij's GUI/macro/plugin machinery -- never in the grey-image path.
 *   colorfields <in.jar> <out.jar>
 *     Rewrite java/awt/Color field refs (any case) to TColor equivalents
 *     in any jar (e.g. jgoodies-forms' FormDebugPanel uses Color.red).
 *     Field renames only; no method changes.
 *   jaxb <in.jar> <out.jar>
 *     Neuter javax.xml.bind.JAXBContext.newInstance overloads to return
 *     null. Many Audiveris classes call newInstance in store/load methods
 *     that TeaVM analyzes (but the demo never calls); newInstance's body
 *     pulls in ContextFinder -> ClassLoader.getResource, which TeaVM's
 *     classlib lacks. Returning null kills the whole JAXB subtree.
 *   jgrapht <in.jar> <out.jar>
 *     Rewrite org.jgrapht.util.SupplierUtil.createSupplier to skip the
 *     Constructor.canAccess check (missing in TeaVM's classlib): replace the
 *     canAccess call with POP, POP, ICONST_1 (pretend accessible).
 *   bsaf <in.jar> <out.jar>
 *     Neuter org.jdesktop.application.ResourceMap's string converters
 *     (Color/Dimension/Point/Rectangle parseString) and loadImageIcon to
 *     return null -- they call Color.decode, Color.<init>(int,boolean),
 *     Dimension.setSize, Point.setLocation and ClassLoader.getResource,
 *     all missing from TeaVM's classlib. UI resource strings only.
 *   phantom <shims.jar>
 *     In-place: rewrite java/lang/ref/PhantomReference's super(referent)
 *     call to super() (TeaVM's TReference has only a no-arg ctor; javac
 *     needs the 1-arg call because JDK Reference has no no-arg ctor).
 */
public class RewriteJars {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("usage: RewriteJars ij|jgrapht|bsaf|jaxb|colorfields|phantom ...");
            System.exit(2);
        }
        switch (args[0]) {
            case "ij":
                rewriteIj(Paths.get(args[1]), Paths.get(args[2]));
                break;
            case "jgrapht":
                rewriteJgraph(Paths.get(args[1]), Paths.get(args[2]));
                break;
            case "bsaf":
                rewriteBsaf(Paths.get(args[1]), Paths.get(args[2]));
                break;
            case "jaxb":
                rewriteJaxb(Paths.get(args[1]), Paths.get(args[2]));
                break;
            case "colorfields":
                rewriteColorFields(Paths.get(args[1]), Paths.get(args[2]));
                break;
            case "phantom":
                rewritePhantom(Paths.get(args[1]));
                break;
            default:
                System.err.println("unknown mode " + args[0]);
                System.exit(2);
        }
    }

    // ---- method neutering ----
    // Replace a method body with a default return (or, for a ctor, a
    // super-call-only body). Used for methods whose bodies reference
    // members TeaVM's classlib lacks, in code the demo never calls.
    // Returns true if the method was neutered.
    static boolean neuterMethod(org.objectweb.asm.tree.ClassNode cn,
            org.objectweb.asm.tree.MethodNode mn, Set<String> keys) {
        if (!keys.contains(cn.name + "." + mn.name)) return false;
        mn.instructions.clear();
        mn.tryCatchBlocks.clear();
        mn.localVariables.clear();
        mn.visibleAnnotations = null;
        mn.invisibleAnnotations = null;
        if (mn.name.equals("<init>")) {
            // Super-call-only body. The only neutered ctors are
            // PluginClassLoader's, whose super is URLClassLoader; our shim
            // has a (URL[]) ctor and tolerates a null array.
            mn.instructions.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ALOAD, 0));
            mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.ACONST_NULL));
            mn.instructions.add(new org.objectweb.asm.tree.MethodInsnNode(Opcodes.INVOKESPECIAL,
                    cn.superName, "<init>", "([Ljava/net/URL;)V", false));
            mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.RETURN));
        } else if (mn.name.equals("<clinit>")) {
            mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.RETURN));
        } else {
            char ret = mn.desc.charAt(mn.desc.lastIndexOf(')') + 1);
            switch (ret) {
                case 'V':
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.RETURN));
                    break;
                case 'Z': case 'B': case 'C': case 'S': case 'I':
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.ICONST_0));
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.IRETURN));
                    break;
                case 'J':
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.LCONST_0));
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.LRETURN));
                    break;
                case 'F':
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.FCONST_0));
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.FRETURN));
                    break;
                case 'D':
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.DCONST_0));
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.DRETURN));
                    break;
                default: // object or array
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.ACONST_NULL));
                    mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.ARETURN));
                    break;
            }
        }
        System.out.println("  neutered " + cn.name + "." + mn.name + mn.desc);
        return true;
    }

    // ---- ij: methods to neuter (keys are "owner.name") ----
    // Bodies call classlib-missing members (Color.getRGB/<init>(int,boolean),
    // ClassLoader.loadClass/getResource, System.exit/setSecurityManager,
    // Runtime.exec/maxMemory, Thread.stop/getThreadGroup) in ij's GUI /
    // macro / plugin machinery. None is in the grey-image reading path
    // (ByteProcessor/ImageProcessor core); the demo never calls them.
    static final Set<String> IJ_NEUTER = new HashSet<>(Arrays.asList(
        "ij/gui/Plot.drawLegend",
        "ij/io/RoiEncoder.putHeader2",
        "ij/io/RoiEncoder.saveStrokeWidthAndColor",
        "ij/io/RoiDecoder.getStrokeWidthAndColor",
        "ij/gui/PlotWindow.<clinit>",
        "ij/macro/Functions.doColor",
        "ij/macro/Functions.getColorValue",
        "ij/macro/Functions.getValue",
        "ij/macro/Functions.call",
        "ij/macro/Functions.exec",
        "ij/plugin/Colors.getHexString",
        "ij/plugin/Colors.decode",
        "ij/process/ColorProcessor.setColor",
        "ij/process/FloatProcessor.setColor",
        "ij/process/ShortProcessor.setColor",
        "ij/util/Tools.c2hex",
        "ij/util/Tools.copyFile",
        "ij/util/Tools.getHash",
        "ij/IJ.runUserPlugIn",
        "ij/IJ.getImage",
        "ij/IJ.outOfMemory",
        "ij/Menus.setupPluginsAndMacrosPaths",
        "ij/macro/Interpreter.abortAllMacroThreads",
        "ij/plugin/ImageInfo.getExifData",
        "ij/plugin/Memory.maxMemory",
        "ij/io/Opener.openUsingBioFormats",
        "ij/io/PluginClassLoader.<init>",
        "ij/io/OpenDialog.open",
        "ij/plugin/frame/RoiManager.getHex",
        "ij/gui/ImageCanvas.getShowAllColor"
    ));

    // ---- ij: Color field refs ----
    static final Map<String, String> COLOR_MAP = new HashMap<>();
    static {
        COLOR_MAP.put("black", "BLACK");
        COLOR_MAP.put("white", "WHITE");
        COLOR_MAP.put("lightGray", "WHITE"); // approx: no LIGHT_GRAY in TColor
        COLOR_MAP.put("gray", "WHITE");      // approx
        COLOR_MAP.put("darkGray", "BLACK");  // approx
        COLOR_MAP.put("red", "BLACK");       // approx (GUI-only use in ij)
        COLOR_MAP.put("green", "BLACK");     // approx
        COLOR_MAP.put("blue", "BLACK");      // approx
        COLOR_MAP.put("yellow", "BLACK");    // approx
        COLOR_MAP.put("magenta", "BLACK");   // approx
        COLOR_MAP.put("cyan", "BLACK");      // approx
        COLOR_MAP.put("orange", "BLACK");    // approx
        COLOR_MAP.put("pink", "BLACK");      // approx
        // Uppercase variants (TColor has only BLACK/WHITE as constants)
        COLOR_MAP.put("LIGHT_GRAY", "WHITE");
        COLOR_MAP.put("GRAY", "WHITE");
        COLOR_MAP.put("DARK_GRAY", "BLACK");
        COLOR_MAP.put("RED", "BLACK");
        COLOR_MAP.put("GREEN", "BLACK");
        COLOR_MAP.put("BLUE", "BLACK");
        COLOR_MAP.put("YELLOW", "BLACK");
        COLOR_MAP.put("MAGENTA", "BLACK");
        COLOR_MAP.put("CYAN", "BLACK");
        COLOR_MAP.put("ORANGE", "BLACK");
        COLOR_MAP.put("PINK", "BLACK");
    }

    static void rewriteIj(Path in, Path out) throws Exception {
        Map<String, Integer> rewritten = new TreeMap<>();
        Map<String, Integer> otherColorRefs = new TreeMap<>();
        Map<String, Integer> untouched = new TreeMap<>();
        int[] focusFixes = {0};
        int[] neutered = {0};
        try (JarFile jf = new JarFile(in.toFile())) {
            Files.createDirectories(out.getParent());
            try (JarOutputStream jos = new JarOutputStream(Files.newOutputStream(out))) {
                for (JarEntry e : Collections.list(jf.entries())) {
                    byte[] bytes = jf.getInputStream(e).readAllBytes();
                    if (e.getName().endsWith(".class")) {
                        ClassReader cr = new ClassReader(bytes);
                        org.objectweb.asm.tree.ClassNode cn = new org.objectweb.asm.tree.ClassNode();
                        cr.accept(cn, 0);
                        for (org.objectweb.asm.tree.MethodNode mn : cn.methods) {
                            if (neuterMethod(cn, mn, IJ_NEUTER)) { neutered[0]++; continue; }
                            for (org.objectweb.asm.tree.AbstractInsnNode insn : mn.instructions.toArray()) {
                                if (insn instanceof org.objectweb.asm.tree.FieldInsnNode fin
                                        && fin.owner.equals("java/awt/Color")
                                        && (fin.getOpcode() == Opcodes.GETSTATIC || fin.getOpcode() == Opcodes.PUTSTATIC)) {
                                    String key = cn.name + "." + mn.name + " -> Color." + fin.name;
                                    if (COLOR_MAP.containsKey(fin.name)) {
                                        String to = COLOR_MAP.get(fin.name);
                                        rewritten.merge(key + " => " + to, 1, Integer::sum);
                                        fin.name = to;
                                    } else if (fin.name.equals("BLACK") || fin.name.equals("WHITE")) {
                                        untouched.merge(key, 1, Integer::sum);
                                    } else {
                                        otherColorRefs.merge("FIELD " + key, 1, Integer::sum);
                                    }
                                } else if (insn instanceof org.objectweb.asm.tree.MethodInsnNode min
                                        && min.owner.equals("java/awt/Color")) {
                                    otherColorRefs.merge("METHOD " + cn.name + "." + mn.name + " -> Color." + min.name + min.desc, 1, Integer::sum);
                                } else if (insn instanceof org.objectweb.asm.tree.MethodInsnNode min
                                        && min.name.equals("requestFocus") && min.desc.equals("()V")) {
                                    // ij was compiled against a Component.requestFocus()V;
                                    // the JDK (and TeaVM) has requestFocus()Z. Retarget the
                                    // call and discard the boolean result (stack-neutral).
                                    min.owner = "java/awt/Component";
                                    min.desc = "()Z";
                                    mn.instructions.insert(insn, new org.objectweb.asm.tree.InsnNode(Opcodes.POP));
                                    focusFixes[0]++;
                                }
                            }
                        }
                        // Recompute frames: the POP insertions shift bytecode
                        // offsets, so the original StackMapTable is stale.
                        // (Copying frames was the likely cause of the Node
                        // WasmGC validation failure in the round-7 wasm.)
                        ClassWriter cw = new SafeClassWriter(ClassWriter.COMPUTE_FRAMES);
                        cn.accept(cw);
                        bytes = cw.toByteArray();
                    }
                    JarEntry ne = new JarEntry(e.getName());
                    ne.setTime(e.getTime());
                    jos.putNextEntry(ne);
                    jos.write(bytes);
                    jos.closeEntry();
                }
            }
        }
        System.out.println("== ij Color field rewrites (" + rewritten.values().stream().mapToInt(i -> i).sum() + ") ==");
        rewritten.forEach((k, v) -> System.out.println("  " + v + "x " + k));
        System.out.println("== ij Color refs left untouched (BLACK/WHITE, " + untouched.values().stream().mapToInt(i -> i).sum() + ") ==");
        untouched.forEach((k, v) -> System.out.println("  " + v + "x " + k));
        System.out.println("== ij OTHER Color member refs (need attention, " + otherColorRefs.values().stream().mapToInt(i -> i).sum() + ") ==");
        otherColorRefs.forEach((k, v) -> System.out.println("  " + v + "x " + k));
        System.out.println("== ij requestFocus()V -> ()Z + POP fixes: " + focusFixes[0] + " ==");
        System.out.println("== ij neutered methods: " + neutered[0] + " ==");
        System.out.println("wrote " + out);
    }

    // ---- colorfields: Color field rewrites only, any jar ----
    static void rewriteColorFields(Path in, Path out) throws Exception {
        Map<String, Integer> rewritten = new TreeMap<>();
        Map<String, Integer> untouched = new TreeMap<>();
        try (JarFile jf = new JarFile(in.toFile())) {
            Files.createDirectories(out.getParent());
            try (JarOutputStream jos = new JarOutputStream(Files.newOutputStream(out))) {
                for (JarEntry e : Collections.list(jf.entries())) {
                    byte[] bytes = jf.getInputStream(e).readAllBytes();
                    if (e.getName().endsWith(".class")) {
                        ClassReader cr = new ClassReader(bytes);
                        org.objectweb.asm.tree.ClassNode cn = new org.objectweb.asm.tree.ClassNode();
                        cr.accept(cn, 0);
                        for (org.objectweb.asm.tree.MethodNode mn : cn.methods) {
                            for (org.objectweb.asm.tree.AbstractInsnNode insn : mn.instructions.toArray()) {
                                if (insn instanceof org.objectweb.asm.tree.FieldInsnNode fin
                                        && fin.owner.equals("java/awt/Color")
                                        && (fin.getOpcode() == Opcodes.GETSTATIC || fin.getOpcode() == Opcodes.PUTSTATIC)) {
                                    String key = cn.name + "." + mn.name + " -> Color." + fin.name;
                                    if (COLOR_MAP.containsKey(fin.name)) {
                                        rewritten.merge(key + " => " + COLOR_MAP.get(fin.name), 1, Integer::sum);
                                        fin.name = COLOR_MAP.get(fin.name);
                                    } else if (fin.name.equals("BLACK") || fin.name.equals("WHITE")) {
                                        untouched.merge(key, 1, Integer::sum);
                                    } else {
                                        System.out.println("  UNMAPPED Color field (left as-is): " + key);
                                    }
                                }
                            }
                        }
                        ClassWriter cw = new ClassWriter(cr, 0);
                        cn.accept(cw);
                        bytes = cw.toByteArray();
                    }
                    JarEntry ne = new JarEntry(e.getName());
                    ne.setTime(e.getTime());
                    jos.putNextEntry(ne);
                    jos.write(bytes);
                    jos.closeEntry();
                }
            }
        }
        System.out.println("== colorfields rewrites (" + rewritten.values().stream().mapToInt(i -> i).sum() + ") ==");
        rewritten.forEach((k, v) -> System.out.println("  " + v + "x " + k));
        System.out.println("wrote " + out);
    }

    // ---- jaxb: neuter JAXBContext.newInstance overloads ----
    static void rewriteJaxb(Path in, Path out) throws Exception {
        int[] hits = {0};
        try (JarFile jf = new JarFile(in.toFile())) {
            Files.createDirectories(out.getParent());
            try (JarOutputStream jos = new JarOutputStream(Files.newOutputStream(out))) {
                for (JarEntry e : Collections.list(jf.entries())) {
                    byte[] bytes = jf.getInputStream(e).readAllBytes();
                    if (e.getName().endsWith(".class")) {
                        ClassReader cr = new ClassReader(bytes);
                        org.objectweb.asm.tree.ClassNode cn = new org.objectweb.asm.tree.ClassNode();
                        cr.accept(cn, 0);
                        for (org.objectweb.asm.tree.MethodNode mn : cn.methods) {
                            if (cn.name.equals("javax/xml/bind/JAXBContext") && mn.name.equals("newInstance")) {
                                if (neuterMethod(cn, mn, Set.of("javax/xml/bind/JAXBContext.newInstance"))) hits[0]++;
                            }
                        }
                        ClassWriter cw = new SafeClassWriter(ClassWriter.COMPUTE_FRAMES);
                        cn.accept(cw);
                        bytes = cw.toByteArray();
                    }
                    JarEntry ne = new JarEntry(e.getName());
                    ne.setTime(e.getTime());
                    jos.putNextEntry(ne);
                    jos.write(bytes);
                    jos.closeEntry();
                }
            }
        }
        System.out.println("== jaxb JAXBContext.newInstance neuters: " + hits[0] + " ==");
        System.out.println("wrote " + out);
    }

    // ---- bsaf (appframework): neuter ResourceMap string converters ----
    // ResourceMap$*StringConverter.parseString calls Color.decode,
    // Color.<init>(int,boolean), Dimension.setSize, Point.setLocation --
    // all missing from TeaVM's classlib (TColor/TDimension/TPoint are
    // fixed). loadImageIcon calls ClassLoader.getResource (also missing).
    // These feed UI resource strings only; return null instead.
    static final Set<String> BSAF_TARGETS = new HashSet<>(Arrays.asList(
        "org/jdesktop/application/ResourceMap$ColorStringConverter.parseString",
        "org/jdesktop/application/ResourceMap$DimensionStringConverter.parseString",
        "org/jdesktop/application/ResourceMap$PointStringConverter.parseString",
        "org/jdesktop/application/ResourceMap$RectangleStringConverter.parseString",
        "org/jdesktop/application/ResourceMap.loadImageIcon"));

    static void rewriteBsaf(Path in, Path out) throws Exception {
        int[] hits = {0};
        try (JarFile jf = new JarFile(in.toFile())) {
            Files.createDirectories(out.getParent());
            try (JarOutputStream jos = new JarOutputStream(Files.newOutputStream(out))) {
                for (JarEntry e : Collections.list(jf.entries())) {
                    byte[] bytes = jf.getInputStream(e).readAllBytes();
                    if (e.getName().endsWith(".class")) {
                        ClassReader cr = new ClassReader(bytes);
                        org.objectweb.asm.tree.ClassNode cn = new org.objectweb.asm.tree.ClassNode();
                        cr.accept(cn, 0);
                        for (org.objectweb.asm.tree.MethodNode mn : cn.methods) {
                            String key = cn.name + "." + mn.name;
                            if (BSAF_TARGETS.contains(key)) {
                                mn.instructions.clear();
                                mn.tryCatchBlocks.clear();
                                mn.localVariables.clear();
                                mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.ACONST_NULL));
                                mn.instructions.add(new org.objectweb.asm.tree.InsnNode(Opcodes.ARETURN));
                                hits[0]++;
                                System.out.println("  neutered " + key + mn.desc);
                            }
                        }
                        ClassWriter cw = new SafeClassWriter(ClassWriter.COMPUTE_FRAMES);
                        cn.accept(cw);
                        bytes = cw.toByteArray();
                    }
                    JarEntry ne = new JarEntry(e.getName());
                    ne.setTime(e.getTime());
                    jos.putNextEntry(ne);
                    jos.write(bytes);
                    jos.closeEntry();
                }
            }
        }
        System.out.println("== bsaf ResourceMap neuters: " + hits[0] + " ==");
        System.out.println("wrote " + out);
    }

    /** ClassWriter that falls back to java/lang/Object when a common
     *  superclass cannot be loaded (e.g. classes only in the rewritten jar). */
    static class SafeClassWriter extends ClassWriter {
        SafeClassWriter(int flags) { super(flags); }
        @Override
        protected String getCommonSuperClass(String type1, String type2) {
            try {
                return super.getCommonSuperClass(type1, type2);
            } catch (Exception e) {
                return "java/lang/Object";
            }
        }
    }

    // ---- jgrapht: skip Constructor.canAccess ----
    static void rewriteJgraph(Path in, Path out) throws Exception {
        Map<String, Integer> hits = new TreeMap<>();
        try (JarFile jf = new JarFile(in.toFile())) {
            Files.createDirectories(out.getParent());
            try (JarOutputStream jos = new JarOutputStream(Files.newOutputStream(out))) {
                for (JarEntry e : Collections.list(jf.entries())) {
                    byte[] bytes = jf.getInputStream(e).readAllBytes();
                    if (e.getName().equals("org/jgrapht/util/SupplierUtil.class")) {
                        ClassReader cr = new ClassReader(bytes);
                        // Recompute frames: the replacement adds instructions,
                        // so the original StackMapTable offsets are stale.
                        ClassWriter cw = new SafeClassWriter(ClassWriter.COMPUTE_FRAMES);
                        cr.accept(new ClassVisitor(Opcodes.ASM9, cw) {
                            @Override
                            public MethodVisitor visitMethod(int acc, String name, String desc, String sig, String[] ex) {
                                MethodVisitor mv = super.visitMethod(acc, name, desc, sig, ex);
                                return new MethodVisitor(Opcodes.ASM9, mv) {
                                    @Override
                                    public void visitMethodInsn(int op, String owner, String mname, String mdesc, boolean itf) {
                                        if (owner.equals("java/lang/reflect/Constructor") && mname.equals("canAccess")) {
                                            // stack: [constructor, arg] -> boolean.
                                            // Replace with: POP, POP, ICONST_1 (pretend accessible).
                                            hits.merge("SupplierUtil.createSupplier canAccess", 1, Integer::sum);
                                            super.visitInsn(Opcodes.POP);
                                            super.visitInsn(Opcodes.POP);
                                            super.visitInsn(Opcodes.ICONST_1);
                                            return;
                                        }
                                        super.visitMethodInsn(op, owner, mname, mdesc, itf);
                                    }
                                };
                            }
                        }, 0);
                        bytes = cw.toByteArray();
                    }
                    JarEntry ne = new JarEntry(e.getName());
                    ne.setTime(e.getTime());
                    jos.putNextEntry(ne);
                    jos.write(bytes);
                    jos.closeEntry();
                }
            }
        }
        System.out.println("== jgrapht canAccess rewrites: " + hits + " ==");
        System.out.println("wrote " + out);
    }

    // ---- phantom: super(referent) -> super() ----
    // The ctor bytecode is: aload_0; aload_1; invokespecial Reference.<init>(Object)V
    // Changing only the descriptor would leave the aload_1 value on the stack,
    // so remove that load too (tree API) and switch the descriptor to ()V.
    static void rewritePhantom(Path jarPath) throws Exception {
        Path tmp = jarPath.resolveSibling(jarPath.getFileName() + ".tmp");
        int[] hits = {0};
        try (JarFile jf = new JarFile(jarPath.toFile());
             JarOutputStream jos = new JarOutputStream(Files.newOutputStream(tmp))) {
            for (JarEntry e : Collections.list(jf.entries())) {
                byte[] bytes = jf.getInputStream(e).readAllBytes();
                if (e.getName().equals("java/lang/ref/PhantomReference.class")) {
                    ClassReader cr = new ClassReader(bytes);
                    org.objectweb.asm.tree.ClassNode cn = new org.objectweb.asm.tree.ClassNode();
                    cr.accept(cn, 0);
                    for (org.objectweb.asm.tree.MethodNode mn : cn.methods) {
                        if (!mn.name.equals("<init>")) continue;
                        for (org.objectweb.asm.tree.AbstractInsnNode insn : mn.instructions.toArray()) {
                            if (insn instanceof org.objectweb.asm.tree.MethodInsnNode min
                                    && min.owner.equals("java/lang/ref/Reference")
                                    && min.name.equals("<init>")
                                    && min.desc.equals("(Ljava/lang/Object;)V")) {
                                org.objectweb.asm.tree.AbstractInsnNode prev = insn.getPrevious();
                                if (!(prev instanceof org.objectweb.asm.tree.VarInsnNode vin)
                                        || vin.getOpcode() != Opcodes.ALOAD) {
                                    throw new IllegalStateException("PhantomReference ctor: expected ALOAD before super call, got " + prev);
                                }
                                mn.instructions.remove(prev);
                                min.desc = "()V";
                                hits[0]++;
                            }
                        }
                    }
                    ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES);
                    cn.accept(cw);
                    bytes = cw.toByteArray();
                }
                JarEntry ne = new JarEntry(e.getName());
                ne.setTime(e.getTime());
                jos.putNextEntry(ne);
                jos.write(bytes);
                jos.closeEntry();
            }
        }
        Files.move(tmp, jarPath, StandardCopyOption.REPLACE_EXISTING);
        System.out.println("== phantom super() rewrites: " + hits[0] + " (in " + jarPath + ") ==");
    }
}
