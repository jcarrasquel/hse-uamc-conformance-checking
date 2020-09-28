package com.pais.fix;

import java.text.ParseException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class Event {
	
	protected String activity;
	
	protected LocalDateTime timestamp;
	
	public Event(String activity, String timestamp) throws ParseException{
		if(activity != null){
			setActivityName(activity);
		}else{
			this.activity = "submit";
		}
		DateTimeFormatter myFormatter = DateTimeFormatter.ofPattern("yyyyMMdd-HH:mm:ss.SSSSSS");
		//20190218-02:14:43.357922
		this.timestamp = LocalDateTime.parse(timestamp, myFormatter);
	}
	
	public String getTimestamp() {
		
		return timestamp.format(DateTimeFormatter.ofPattern("dd-MM-yyyy'T'HH:mm:ss.SSSSSS"));
	}
	
	private void setActivityName(String activity){
		this.activity = activity;
		if(activity.equalsIgnoreCase("0")){
			this.activity = "new";
		}
		if(activity.equalsIgnoreCase("C")){
			this.activity = "expire";
		}
		if(activity.equalsIgnoreCase("4")){
			this.activity = "cancel";
		}
		if(activity.equalsIgnoreCase("D")){
			this.activity = "restart";
		}
		if(activity.equalsIgnoreCase("5")){
			this.activity = "replace";
		}
		if(activity.equalsIgnoreCase("F")){
			this.activity = "trade";
		}
		if(activity.equalsIgnoreCase("H")){
			this.activity = "trade_cancel";
		}
		if(activity.equalsIgnoreCase("8")){
			this.activity = "reject";
		}
		if(activity.equalsIgnoreCase("9")){
			this.activity = "suspend";
		}
	}
	
	public String getActivity() {
		return activity;
	}

	public void setActivity(String activity) {
		this.activity = activity;
	}

}