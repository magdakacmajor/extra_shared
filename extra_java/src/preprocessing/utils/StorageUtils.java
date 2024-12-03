package preprocessing.utils;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

import preprocessing.obj.RawDocument;

public class StorageUtils {
//	private static Logger logger = LoggerFactory.getLogger(StorageUtils.class);

	
	public static List<RawDocument> getAllDocuments(String filePath){
		Gson gson = new Gson();
		return FileUtils.listFiles(new File(filePath), null, false)
		 		  .stream().map(file -> {
						try {
							return gson.fromJson(FileUtils.readFileToString(file, StandardCharsets.UTF_8), RawDocument.class);
						} catch (JsonSyntaxException | IOException e1) {
//							LoggingUtils.error(logger, "Failed to read file " + file.getName(), e1);
							System.out.println("Failed to read file " + file.getName());
							System.out.println(e1.getMessage());
							return null;
						}
		 		  	}).collect(Collectors.toList());
	}
	
	public static void updateDocuments(String filePath, List<RawDocument>docs){
		Gson gson = new Gson();
		docs.stream().collect(Collectors.toMap(RawDocument::get_id, doc -> gson.toJson(doc)))
					 .forEach((id, body) -> {
								try {
									Files.write(Paths.get(filePath, id ), body.getBytes());
								} catch (IOException e) {
//									LoggingUtils.error(logger, "Failed to write file " + id, e);
									System.out.println("Failed to write file " + id);
									System.out.println(e.getMessage());
								}
							});		
	}
}
