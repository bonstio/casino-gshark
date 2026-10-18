import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;
import java.io.File;

public class ValidateTest {
    public static void main(String[] args) {
        if (args.length < 2) {
            System.out.println("Usage: java ValidateTest <xsdPath> <xmlPath>");
            return;
        }
        String xsdPath = args[0];
        String xmlPath = args[1];
        System.out.println("Validating " + xmlPath + " against " + xsdPath);
        try {
            System.setProperty("javax.xml.validation.SchemaFactory:http://www.w3.org/XML/XMLSchema/v1.1",
                "org.apache.xerces.jaxp.validation.XMLSchema11Factory");
            SchemaFactory factory = SchemaFactory.newInstance("http://www.w3.org/XML/XMLSchema/v1.1");
            Schema schema = factory.newSchema(new File(xsdPath));
            Validator validator = schema.newValidator();
            final int[] errorCount = {0};
            validator.setErrorHandler(new ErrorHandler() {
                public void warning(SAXParseException e) {
                    System.out.println("[WARNING Line " + e.getLineNumber() + ":Col " + e.getColumnNumber() + "]: " + e.getMessage());
                }
                public void error(SAXParseException e) {
                    errorCount[0]++;
                    // if (errorCount[0] <= 30) {
                        System.out.println("[ERROR Line " + e.getLineNumber() + ":Col " + e.getColumnNumber() + "]: " + e.getMessage());
                    }
                // }
                public void fatalError(SAXParseException e) throws SAXException {
                    errorCount[0]++;
                    System.out.println("[FATAL Line " + e.getLineNumber() + ":Col " + e.getColumnNumber() + "]: " + e.getMessage());
                }
            });
            validator.validate(new StreamSource(new File(xmlPath)));
            if (errorCount[0] == 0) {
                System.out.println("SUCCESS: VALIDATION PASSED WITH 0 ERRORS!");
            } else {
                System.out.println("FAILED: Total " + errorCount[0] + " errors found.");
            }
        } catch (Exception e) {
            System.out.println("EXCEPTION: " + e);
            e.printStackTrace();
        }
    }
}
