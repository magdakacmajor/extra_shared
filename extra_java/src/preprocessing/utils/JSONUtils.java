package preprocessing.utils;

import java.util.HashMap;

import com.google.gson.Gson;
import com.google.gson.JsonObject;

public class JSONUtils {
	
	private static Gson gson = new Gson();
	
	@SuppressWarnings("unchecked")
	public static JsonObject mergeJsonObjects(JsonObject jo1, JsonObject jo2){
		HashMap<String, String> jo1Map = gson.fromJson(jo1, HashMap.class);
		jo1Map.putAll(gson.fromJson(jo2, HashMap.class));
		
		return (JsonObject) gson.toJsonTree(jo1Map);
	}
}
