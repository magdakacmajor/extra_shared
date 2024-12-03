package preprocessing.utils;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

//import org.slf4j.Logger;
//import org.slf4j.LoggerFactory;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import preprocessing.obj.JavaTestClass;
import preprocessing.obj.RawDocument;
import preprocessing.obj.SizeBounds;


public class DataPrepUtils {
	
	public final static String SRC_CORPUS = "corpus.nl";
	public final static String TGT_CORPUS = "corpus.pl";
	public final static String IDS = "corpus.ids";
	
//	private static Logger logger = LoggerFactory.getLogger(DataPrepUtils.class); 
	
	public static void writeCorpora(String filePath,
									String outputDir,
									boolean addComments,
									SizeBounds sb) throws IOException{
		List<RawDocument> docs = StorageUtils.getAllDocuments(filePath);
		DataPrepUtils.writeCorpora(docs, outputDir, addComments, sb);
	}
	
	public static void writeCorpora(List<RawDocument> docs,
									String outputDir,
									boolean addComments,
									SizeBounds sb) throws IOException{

		if(sb !=null){
			outputDir = String.join(File.separator, outputDir, String.join("-", "src", sb.getSrcLower()+"", sb.getSrcUpper()+"", 
																				"tgt", sb.getTgtLower()+"", sb.getTgtUpper()+""));
		}
		Files.createDirectories(Paths.get(outputDir));
		PrintWriter srcWriter = new PrintWriter(String.join(File.separator,
															outputDir, 
															SRC_CORPUS));
		PrintWriter tgtWriter = new PrintWriter(String.join(File.separator, 
															outputDir, 
															TGT_CORPUS));
		PrintWriter idWriter = new PrintWriter(String.join(File.separator, outputDir,IDS));
		
		Set<String> nonDuplicates = new HashSet<String>();
		int c = 0;
		for (RawDocument doc : docs){
			try {
				Iterator<JsonElement> it = doc.getParsedTestCases().iterator();
				while(it.hasNext()){
					JsonObject testcase = it.next().getAsJsonObject();
					String srcSequence = String.join(" ", "#class", testcase.get("classNameNL").getAsString(), 
													   "#method", testcase.get("title").getAsString(),
													   addComments ? 
															   testcase.get("allContainedComments")
															   		   .getAsString()
															   		   .replaceAll("\\n+", " ")
															   		   .replaceAll("\\s+", " ")
															   : "").trim();
					String tgtSequence = testcase.get("body").getAsString()
															 .replaceAll("([().;,={}\"\"<>+:\\-\\[\\]/\\\\])", " $1 ")
														//	 .replaceAll("(\\W)", " $1 ")
															 .replaceAll("\\n+", " ")
															 .replaceAll("\\s+", " ").trim();
					
					if(outOfBounds(sb, srcSequence.split("\\s").length, tgtSequence.split("\\s").length)){
						c++;
						System.out.println(srcSequence);
						continue;
					}
					
					if(!nonDuplicates.add(srcSequence)) {
//						logger.info(srcSequence);
						System.out.println(srcSequence);
						continue;
					}
					
					srcWriter.println(srcSequence);
					tgtWriter.println(tgtSequence);
					//mapping between corpus lines and original test cases
					idWriter.println(doc.get_id() + "," + testcase.get("id").getAsString());
					
				}
			} catch(Exception e){
//				logger.error(doc.get_id(), e);
				System.out.println(doc.get_id());
				System.out.println(e);
			}
			srcWriter.flush();
			tgtWriter.flush();
			idWriter.flush();
		}
//		logger.info("Corpus size:"+nonDuplicates.size());
//		logger.info("Num of sequences rejected because of size: " + c);
		System.out.println("Corpus size:"+nonDuplicates.size());
		System.out.println("Num of sequences rejected because of size: " + c);
		srcWriter.close();
		tgtWriter.close();
		idWriter.close();
	}
	
	//lower bound inclusive, upper bound exclusive
	private static boolean outOfBounds (SizeBounds sb, int srcLen, int tgtLen){
		try{
			if(srcLen < sb.getSrcLower() ||
			   srcLen >= sb.getSrcUpper() ||
			   tgtLen < sb.getTgtLower() ||
			   tgtLen >= sb.getTgtUpper() ) {
					return true;
			}
			return false;

		}catch(NullPointerException e){
			return false;
		}
	}
	
	public static void parseJavaClasses(String filePath) {
		List<RawDocument> rawDocs = StorageUtils.getAllDocuments(filePath);
		DataPrepUtils.parseJavaClasses(rawDocs);
		StorageUtils.updateDocuments(filePath, rawDocs);
	}
	
	/**
	 * wrapper to support for jython integration
	 * @param rawDocs array of RawDoc objects
	 * @return array of parsed objects
	 */
	public static RawDocument[] parseJavaClassesJython(RawDocument[] rawDocsArray) {
		List<RawDocument> rawDocs = Arrays.asList(rawDocsArray);
		parseJavaClasses(rawDocs);
		return rawDocs.stream().toArray(RawDocument[]::new);
	}


	public static void parseJavaClasses(List<RawDocument> rawDocs) {
		for(RawDocument rawDoc : rawDocs){
			JsonArray parsedTestCases = new JsonArray();
			for (Map<String, String> rawClass : rawDoc.getRawClasses()){
				try {
					System.out.println ("Processing class: " + rawClass.keySet().iterator().next());
					rawClass.entrySet()
							.stream()
							.filter(rc -> rc.getKey().endsWith(".java"))
							.forEachOrdered(rc -> {
									JavaTestClass tclass = new JavaTestClass();
									tclass.parseTestClass(rc.getValue());
									JsonObject tclassJson = (JsonObject) (new Gson().toJsonTree(tclass));
									tclassJson.remove("testCases");
									tclass.getTestCases()
										  .stream()
										  .forEachOrdered(tcase -> {
											  	JsonObject mergedJson =JSONUtils.mergeJsonObjects(
											  			(JsonObject) new Gson().toJsonTree(tcase),tclassJson);
											  	mergedJson.addProperty("origin_url", rawDoc.getOrigin_url());
											  	mergedJson.addProperty("filepath", rawDoc.getFilepath());
											  	parsedTestCases.add(mergedJson);
										  });																   			
									});
				}catch(Exception e){
//					LoggingUtils.error(logger, "Failed to process class " + rawClass.keySet().toString(), e);
					System.out.println("Failed to process class " + rawClass.keySet().toString());
					System.out.println(e.getStackTrace());
				}
			}
			
			rawDoc.setParsedTestCases(parsedTestCases);
		}
		System.out.println("rawDocs in Java: " + rawDocs.size());
	}

/*
	public static void parseCuts(String filePath) {
		List<RawDocument> rawDocs = StorageUtils.getAllDocuments(filePath);
		DataPrepUtils.parseCuts(rawDocs);
		StorageUtils.updateDocuments(filePath, rawDocs);
	}
	
	public static void parseCuts(List<RawDocument> rawDocs){
		for(RawDocument rawDoc : rawDocs){
//			JsonArray parsedTestCases = new JsonArray();
			Entry<String, String> rawClassEntry = rawDoc.getRawClasses().get(0).entrySet().iterator().next();
			try {
				JavaTestClass tclass = new JavaTestClass();
				tclass.parseTestClass(rawClassEntry.getValue());
				rawDoc.setPackageName(tclass.getPackageName());
				rawDoc.setStoryId(rawDoc.get_id());
				rawDoc.setStoryName(tclass.getClassNameNL());
				rawDoc.setShortDesc(tclass.getClassJavadocComment());
				logger.info(rawDoc.get_id());
			}catch(Exception e){
				LoggingUtils.error(logger, "Failed to process class " + rawDoc.get_id(), e);
			}
		}
	} */
}
