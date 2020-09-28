package com.pais.fix;

import java.util.HashMap;
import java.util.Map;

public class FIXMessage {
	
	private Map<Integer, String> fields;
	
	private Boolean invalid;
	
	public String getField(Integer tag){
		return fields.containsKey(tag) ? fields.get(tag) : null;
	}
	
	public Boolean getInvalidFlag(){
		return invalid;
	}
	
	public String print(){
		return fields.toString();
	}
	
	public FIXMessage(int number, String fixMessage) throws Exception{
		
		invalid = false;
		
		Character c = 0x01;
		
		String[] aux = fixMessage.split(c.toString());
		
		fields = new HashMap<Integer, String>();
		int i = 0;
		//try{
		while(i < aux.length){
			String[] pair = aux[i].split("=");
			if(pair.length <= 1){
				invalid = true;
			}else{
				fields.put(Integer.parseInt(pair[0]), pair[1]);
			}
			i++;
		}
		/*}catch(Exception e){
			System.out.println("Exception on message " + number + " data=" + Arrays.toString(aux[i].split("=")));
			//System.out.println((Arrays.toString(aux)));
			//e.printStackTrace();
		}*/
	}
}
