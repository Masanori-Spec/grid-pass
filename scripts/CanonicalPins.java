import java.io.ByteArrayOutputStream;
import java.io.ObjectOutputStream;
import java.util.Base64;

/** Test-only encoder of fixed trusted Integers. Never reads serialized objects. */
class CanonicalPins {
    public static void main(String[] args) throws Exception {
        if (args.length != 0) throw new IllegalArgumentException("No input accepted");
        System.out.println("[");
        for (int i = 0; i < 256; i++) {
            var bytes = new ByteArrayOutputStream();
            try (var stream = new ObjectOutputStream(bytes)) {
                stream.writeObject(Integer.valueOf(i));
            }
            System.out.print("  \"" + Base64.getEncoder().encodeToString(bytes.toByteArray()) + "\"");
            System.out.println(i == 255 ? "" : ",");
        }
        System.out.println("]");
    }
}
