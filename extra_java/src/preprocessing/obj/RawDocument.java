package preprocessing.obj;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.google.gson.JsonArray;

public class RawDocument {
	
	private String _id;
	private String _rev;
	
	private List<Map<String,String>> rawClasses = new ArrayList<Map<String, String>>();
	private JsonArray parsedTestCases = new JsonArray();
	private String origin_url;
	private String filepath;
	
	public String get_id() {
		return _id;
	}
	public void set_id(String _id) {
		this._id = _id;
	}
	public String get_rev() {
		return _rev;
	}
	public void set_rev(String _rev) {
		this._rev = _rev;
	}
	public List<Map<String, String>> getRawClasses() {
		return rawClasses;
	}
	public void setRawClasses(List<Map<String, String>> rawClasses) {
		this.rawClasses = rawClasses;
	}
	public JsonArray getParsedTestCases() {
		return parsedTestCases;
	}
	public void setParsedTestCases(JsonArray parsedTestCases) {
		this.parsedTestCases = parsedTestCases;
	}

	public String getOrigin_url() {
		return origin_url;
	}
	public void setOrigin_url(String origin_url) {
		this.origin_url = origin_url;
	}
	
	public String getFilepath() {
		return filepath;
	}
	
	public void setFilepath(String filepath) {
		this.filepath = filepath;
	}
	
}
