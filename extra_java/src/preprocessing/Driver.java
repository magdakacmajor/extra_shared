package preprocessing;

import java.io.IOException;

import preprocessing.obj.SizeBounds;
import preprocessing.utils.DataPrepUtils;



public class Driver {
	
	private final static String PARSE = "parse",
						 WRITE_CORPORA = "write_corpora";

	public static void main(String[] args) throws IOException, InterruptedException{
		if(args[0].equalsIgnoreCase(PARSE)){
			DataPrepUtils.parseJavaClasses(args[1]); 
		}
		if(args[0].equalsIgnoreCase(WRITE_CORPORA)){
			DataPrepUtils.writeCorpora(args[1],
									   args[2],
									   Boolean.parseBoolean(args[3]),
									   args.length < 7? null: new SizeBounds (args[4], args[5], args[6], args[7])); 
			//(String filepath, String outputDir, Boolean addComments, int maxLength)
		}
	}
}
