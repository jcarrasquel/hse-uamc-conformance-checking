/** ===================================================================
 * Laboratory of Process-Aware Information Systems (PAIS Lab)
 * National Research University Higher School of Economics. Moscow, Russia.
 * Author: Julio Cesar Carrasquel. Research Asssistant | PhD Candidate
 * Contact: jcarrasquel@hse.ru 
 * 
 * Program: PAIS Event Log Generation from FIX Messages for Order Books
 * Description: It generates an event log such that each case represents the trading session in an order book.
 * Each case is an order book associated with the trading of a single financial security.
 * Thus, the log is segmented in cases using the financial security identifier.
 * ==================================================================== **/

package com.pais.fix;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.text.ParseException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map.Entry;

import javax.xml.stream.util.EventReaderDelegate;

public class Main {
	
	public static List<FIXMessage> fixMessages;
	
	public static List<String> securityIds;
	
	protected static File tmpFile;
	
	public static void generateOrderEventLog() throws ParseException, IOException{
		
		EventLog eventLog = new EventLog();
		
		String messageType = null, sender = null, orderId = null, activity = null, timestamp = null, instrument = null, orderType = null;
		Integer caseCounter = 0, eventCounter = 0;
		
		String price = null, side = null, qty = null, qty2 = null, receiver = null;
		String state = null;
		String ciOrder = null;
		String tradeId = null;
		
		ArrayList<OrderEvent> newOrders = new ArrayList<OrderEvent>();
		
		for(FIXMessage m : fixMessages){
			
			instrument = m.getField(48);
			messageType = m.getField(35);
			sender = m.getField(49);
			orderId = m.getField(37); // case id
			activity = m.getField(150);
			timestamp = m.getField(60);
			orderType = m.getField(40);
			price = m.getField(44);
			side = m.getField(54);
			qty = m.getField(151);
			qty2 = m.getField(38);
			receiver = m.getField(56);
			state = m.getField(39);
			ciOrder = m.getField(11);	
			tradeId = m.getField(880);
			
			// *** extracting new order messages ***
			if(messageType != null && messageType.equals("D") && sender != null &&
					ciOrder != null && timestamp != null && instrument != null
						&& securityIds.contains(instrument) && (price != null || orderType.equalsIgnoreCase("1")) && side != null && qty2 != null && receiver != null){
				OrderEvent e = new OrderEvent(activity, state, timestamp, price, side, qty2, sender, ciOrder, orderType, instrument);
				newOrders.add(e);
			}
			
			// *** extracting execution report messages ***
			if(messageType != null && messageType.equalsIgnoreCase("8") && sender != null && sender.equalsIgnoreCase("FGW") &&
				orderId != null && activity != null && timestamp != null && instrument != null
					&& securityIds.contains(instrument) && orderType != null 
					&& (price != null || orderType.equalsIgnoreCase("1")) && side != null && qty != null && receiver != null){

				if( ((LinkedHashMap<String, Case>) eventLog.getCases()).containsKey(orderId) == false){
					Case newCase = new Case();
					((LinkedHashMap<String, Case>) eventLog.getCases()).put(orderId, newCase);
					caseCounter++;
				}
				
				OrderEvent e = new OrderEvent(activity, state, timestamp, price, side, qty, receiver, ciOrder, orderType, instrument);
				if(e.getActivity().equalsIgnoreCase("trade") || e.getActivity().equalsIgnoreCase("trade_cancel")){
					e.setTradeId(tradeId);
				}
				((Case) ( (LinkedHashMap<String, Case>) eventLog.getCases()).get(orderId)).addEvent(e); // new event e to the case identified by order id
				eventCounter++;
			}
		}
		
		LinkedHashMap<String,Case> cases = eventLog.getCases();
		
		System.out.println("Constructing cases...");
		
		// *** add new orders messages to the cases ***
		for(int i = 0; i < newOrders.size(); i++){
			for(Entry<String, Case> c : cases.entrySet()){
				ArrayList<Event> events = ( (Case) c.getValue()).getEvents();
				OrderEvent e = (OrderEvent) events.get(0);
				if(e.getCiOrderId().equalsIgnoreCase(newOrders.get(i).getCiOrderId())){
					events.add(0, newOrders.get(i));
					break;
				}
			}
		}
		
		tmpFile = File.createTempFile("tmp-event-log", ".tmp"); 
		FileWriter writer = new FileWriter(tmpFile);
		writer.write("CASE, ORDER, EVENT_ID, ACTIVITY, STATE, TIMESTAMP, CLIENT, SIZE, PRICE, SIDE, SEC_ID, [TRADE_ID]\n");

		int n = 0, k = 1;
		
		/*** UPDATE 5: Inject artificial new event right after a submit activity ***/
		
		/*** UPDATE 6: To put submission times --- let us consider that the submission time of the order is the moment where it was submitted ***/
		for(Entry<String, Case> c : cases.entrySet()){
			OrderEvent lastEvent = null;
			n++;
			ArrayList<Event> events = ( (Case) c.getValue()).getEvents();
			String orderSubmissionTime = null;
			for(int i = 0; i < events.size(); i++){
				OrderEvent e = (OrderEvent) events.get(i);
				if(e.getActivity().equals("submit")){
					orderSubmissionTime = e.getTimestamp(); //FIXME accomodate this! We are putting the submission time on the receiver 
				}
				if(i != 0 && lastEvent.getActivity().equals("submit")){ // inject artificial new activity
					if(e.getActivity().equals("new") == false){
						writer.write(n + "," + c.getKey() + "," + k + "," + "new" + "," + lastEvent.getState() + "," + orderSubmissionTime + "," + orderSubmissionTime + "," + lastEvent.getQty() + "," + (lastEvent.getOrderType().equalsIgnoreCase("market") ? "market" : lastEvent.getPrice()) + "," + lastEvent.getSide() + "," + lastEvent.getSecurityId() + "," + (lastEvent.getTradeId() == null ? "" : lastEvent.getTradeId()) + "\n");
						k++;
					}
				}
				
				//System.out.println(n + "," + c.getKey() + "," + k + "," + e.getActivity() + "," + e.getState() + "," + e.getTimestamp() + "," + e.getReceiver() + "," + e.getQty() + "," + (e.getOrderType().equalsIgnoreCase("market") ? "market" : e.getPrice()) + "," + e.getSide() + "," + e.getSecurityId() + "," + (e.getTradeId() == null ? "" : e.getTradeId()) + "\n");
				writer.write(n + "," + c.getKey() + "," + k + "," + e.getActivity() + "," + e.getState() + "," + e.getTimestamp() + "," + orderSubmissionTime + "," + e.getQty() + "," + (e.getOrderType().equalsIgnoreCase("market") ? "market" : e.getPrice()) + "," + e.getSide() + "," + e.getSecurityId() + "," + (e.getTradeId() == null ? "" : e.getTradeId()) + "\n");
				k++;
				lastEvent = e;
			}
		}
		writer.close();
	}
	
	public static void transformEventLog() throws FileNotFoundException, IOException, ParseException{
		
		System.out.println("Transforming cases...");
		
		EventLog eventLog = new EventLog();
		
		LinkedList<OrderEvent> events = new LinkedList<OrderEvent>();
		
		try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(tmpFile)))) {
			String line = reader.readLine(); // reading header
			while ((line = reader.readLine()) != null) {
				String[] var = line.split(",");
				String order, activity, submissionTime, state, timestamp, instrument, price, side, qty, sender = null, ciOrder = null, trade = null;
				order = var[1];
				activity = var[3];
				state = var[4];
				timestamp = var[5];
				DateTimeFormatter myFormatter = DateTimeFormatter.ofPattern("dd-MM-yyyy'T'HH:mm:ss.SSSSSS");
				LocalDateTime tmp = LocalDateTime.parse(timestamp, myFormatter);
				submissionTime = var[6];
				qty = var[7];
				price = var[8];
				side = var[9];
				instrument = var[10];
				if(var.length > 11){
					trade = var[11];
				}
				OrderEvent e = new OrderEvent(activity, state, tmp.format(DateTimeFormatter.ofPattern("yyyyMMdd-HH:mm:ss.SSSSSS")), price, side, qty, sender, ciOrder, instrument);
				e.setReceiver(submissionTime); //FIXME
				e.setOrderId(order);
				if(e.getActivity().equalsIgnoreCase("trade") || e.getActivity().equalsIgnoreCase ("trade_cancel")){
					e.setTradeId(trade);
				}
				events.add(e);
			}
		}
		
		Collections.sort(events);
		
		// *** merge events whose activity label and trade_id attribute are equal *** 
		String activityLabel1, tradeId1, activityLabel2, tradeId2;
		for(int i = 0; i < events.size(); i++){
			activityLabel1 = events.get(i).getActivity();
			tradeId1 = events.get(i).getTradeId();
			if(tradeId1 != null){
				for(int j = i + 1; j < events.size(); j++){
					activityLabel2 = events.get(j).getActivity();
					tradeId2 = events.get(j).getTradeId();
					if(tradeId2 != null && activityLabel1.equalsIgnoreCase(activityLabel2) && tradeId1.equalsIgnoreCase(tradeId2)){
						events.get(i).setTradeOrder(new Order(events.get(j).getOrderId(), events.get(j).getState(), events.get(j).getQty(), events.get(j).getPrice(), events.get(j).getSide()));
						events.get(i).getTradeOrder().setReceiver(events.get(j).getReceiver());
						events.remove(j);
						break;
					}
				}
			}
			if( ((LinkedHashMap<String, Case>) eventLog.getCases()).containsKey(events.get(i).getSecurityId()) == false){
				Case newCase = new Case();
				((LinkedHashMap<String, Case>) eventLog.getCases()).put(events.get(i).getSecurityId(), newCase);
			}
			eventLog.getCases().get(events.get(i).getSecurityId()).addEvent(events.get(i));
		}
		
		PrintWriter writer = new PrintWriter("order-books-event-log.csv", "UTF-8");
		
		writer.println("CASE, TIMESTAMP, ACTIVITY, ID1, TSUB1, PRICE1, QTY1, ID2, TSUB2, PRICE2, QTY2");
		
		/*** UPDATE (4): Filter cases with activities replace and trade_cancel ***/ 
		
		List<String> casesToFilter = new LinkedList<String>();
		
		for(Entry<String, Case> c : eventLog.getCases().entrySet()){
			ArrayList<Event> caseEvents = ( (Case) c.getValue()).getEvents();
			for(int i = 0; i < caseEvents.size(); i++){
				OrderEvent e = (OrderEvent) caseEvents.get(i);
				if(e.getActivity().equalsIgnoreCase("trade_cancel") || e.getActivity().equalsIgnoreCase("replace")){
					casesToFilter.add(c.getKey());
					break;
				}
			}
		}
	
		String activityName, tradeActivityName;
		System.out.println(eventLog.getCases().entrySet().size());
		for(Entry<String, Case> c : eventLog.getCases().entrySet()){
			if(casesToFilter.contains(c.getKey()) == false){
				ArrayList<Event> caseEvents = ( (Case) c.getValue()).getEvents();
				for(int i = 0; i < caseEvents.size(); i++){
					OrderEvent e = (OrderEvent) caseEvents.get(i);
					
					/*** UPDATE (1): Activity name according to the activity name ***/ 
					activityName = updateActivityName(e.getActivity(), e.getSide());
					
					if(e.getTradeOrder() == null){
						writer.println(e.getSecurityId() + "," +  e.getTimestamp2() + "," + activityName + "," + e.getOrderId() + "," + e.getReceiver() + "," + e.getPrice() + "," + e.getQty());
					}else{
						
						/*** UPDATE (3): Trade activity name according to the number of stocks ***/ 
						tradeActivityName = updateTradeActivityName(e.getActivity(), e.getSide(), Integer.parseInt(e.getQty()), e.getTradeOrder().getSide(), e.getTradeOrder().getCurrentSize());
						
						writer.println(e.getSecurityId() + "," + e.getTimestamp2() + "," + tradeActivityName + "," + e.getOrderId() + "," + e.getReceiver() + "," + e.getPrice() + "," + e.getQty() + "," +
						e.getTradeOrder().getIdentifier() + "," + e.getTradeOrder().getReceiver() + "," + (e.getTradeOrder().getPrice() == Double.MAX_VALUE ? "market" : e.getPrice()) + "," + e.getTradeOrder().getCurrentSize());
					}
				}
			}
		}
		writer.close();
	}
	
	public static String updateTradeActivityName(String defaultName, String sideOrder1, Integer qtyOrder1, String sideOrder2, Integer qtyOrder2){
		
		String tradeActivity = null;
		if(qtyOrder1 == 0 && qtyOrder2 == 0){
			tradeActivity = "trade1";
		}else if((sideOrder1.equals("buy") && qtyOrder1 == 0) || (sideOrder2.equals("buy") && qtyOrder2 == 0)){
			tradeActivity = "trade3";
		}else if((sideOrder2.equals("sell") && qtyOrder2 == 0) || (sideOrder1.equals("sell") && qtyOrder1 == 0)){
			tradeActivity = "trade2";
		}
		if(tradeActivity == null){
			System.out.println(defaultName);
			return defaultName;
		}
		return tradeActivity;
	}
	
	public static String updateActivityName(String activityName, String side){
		String res = null;
		if(side.equalsIgnoreCase("buy")){
			if(activityName.equals("submit")) res = "submit buy order";
			else if(activityName.equals("new")) res = "new buy order";
			else if(activityName.equals("cancel") | activityName.equals("expire") || activityName.equals("reject")) res = "discard buy order";
		}else{
			if(activityName.equals("submit")) res = "submit sell order";
			else if(activityName.equals("new")) res = "new sell order";
			else if(activityName.equals("cancel") | activityName.equals("expire") || activityName.equals("reject")) res = "discard sell order";
		}
		if(res == null){
			return activityName;
		}
		return res;
	}
	
	public static void readSecurityNamesFromFile(String securitiesFilename) throws IOException{
		BufferedReader br = Files.newBufferedReader(Paths.get(securitiesFilename));
		String line;      
		while ((line = br.readLine()) != null) {
			securityIds.add(line);
       }
	}
	
	public static void main(String[] args) throws ParseException, IOException{
		
		System.out.println("Laboratory of Process-Aware Information Systems (PAIS Lab). Moscow, Russia.");		
		System.out.println("Order-Books-based Event Log Generator");
		System.out.println("*************************************");
		
		//String fixMessagesFilename = args[0];
		//String securitiesFilename = args[1];
		
		String fixMessagesFilename = "/home/giulio/Desktop/AIST/playground/fix-messages.pcap";
		String securitiesFilename = "/home/giulio/Desktop/AIST/playground/security_list.txt";
		
		System.out.println("Retrieving FIX messages from TCP segment payloads in capture file = " + fixMessagesFilename);
		fixMessages = new LinkedList<FIXMessage>();
		FIXParser.getFIXMessages(fixMessagesFilename, fixMessages);
		System.out.println("FIX messages retrieved!");
		
		System.out.println("Reading financial security identifiers from file = " + securitiesFilename);
		securityIds = new LinkedList<String>();
		readSecurityNamesFromFile(securitiesFilename);
		
		System.out.println("Executing order books event log generation...");
		generateOrderEventLog();
		transformEventLog();
		System.out.println("Event log generation completed!");
	}
	
}