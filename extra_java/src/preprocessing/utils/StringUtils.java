package preprocessing.utils;

public class StringUtils {

	public static String extractNLWords(String camelCaseName) {
		return String.join(" ", 
									 org.apache.commons.lang3.StringUtils.splitByCharacterTypeCamelCase(camelCaseName))
							  .replaceAll(" _ ", " ")
							  .toLowerCase();
				}
	
	public static String stripQuotes (String quotedString){
		return quotedString.replaceAll("^\"|\"$", "");
	}
}
