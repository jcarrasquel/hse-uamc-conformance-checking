/** ===================================================================
 * Laboratory of Process-Aware Information Systems (PAIS Lab)
 * National Research University Higher School of Economics. Moscow, Russia.
 * Author: Julio Cesar Carrasquel. Research Asssistant | PhD Candidate
 * Contact: jcarrasquel@hse.ru 
 * 
 * Program: Extract FIX messages from TCP segment payloads
 * ==================================================================== **/

package com.pais.fix;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import io.pkts.PacketHandler;
import io.pkts.Pcap;
import io.pkts.packet.Packet;
import io.pkts.packet.TCPPacket;
import io.pkts.protocol.Protocol;

public class FIXParser {
	
	protected static int tcpSegments = 0;

	protected static int totalFIXMessages = 0;
	
	protected static int correctFIXMessages = 0;
	
	protected static int n = 0;				/* number of FIX messages parsed */
	
	protected static int wrongMessages = 0;	/* number of invalid FIX messages whose parsing has raised an exception */
	
	public static void getFIXMessages(String fixMessagesFilename, List<FIXMessage> fixMessages) throws FileNotFoundException, UnsupportedEncodingException{	
		
		Pcap pcap = null;
		
		try{
			pcap = Pcap.openStream(new File(fixMessagesFilename));
			pcap.loop(new PacketHandler() {
				
				// Used in the case we are accumulating previous payload for FIX messages being delivered in multiple TCP segments
				String accumPayload = null;
				Boolean accumFlag = false;
				String accumIPAddress = null;			
								
				public boolean nextPacket(Packet packet) throws IOException {
					n++;
			        if (packet.hasProtocol(Protocol.TCP)) {
			        	tcpSegments++;
			        	TCPPacket tcpPacket = (TCPPacket) packet.getPacket(Protocol.TCP);
			            if (tcpPacket.getPayload() != null && n != 237825 /*FIXME specific to the given data set February 2019*/) {
			            	String tcpPayload = null;
			            	if(accumFlag == true){
			            		if(accumIPAddress.equalsIgnoreCase(tcpPacket.getSourceIP())){
					            	tcpPayload = accumPayload != null ? accumPayload + tcpPacket.getPayload().toString() : tcpPacket.getPayload().toString();
			            			accumFlag = false;
			            		}else{
			            			tcpPayload = tcpPacket.getPayload().toString();
			            		}
			            	}else{
			            		tcpPayload = tcpPacket.getPayload().toString();
			            	}
			            	// Take the payload and create FIX messages as long as you have have '10=CHK' (checksum) substrings */
		            		Matcher matcher = Pattern.compile("10=\\d{3}").matcher(tcpPayload);
		            		int li = 0, ls = 0;
		            		while(matcher.find()){
		            			ls = matcher.start() + 8;
		            			String fixMessage = tcpPayload.substring(li, ls);
		            			FIXMessage fixMessageObject = null;
		            			try{
		            				fixMessageObject = new FIXMessage(n, fixMessage);
		            				totalFIXMessages++;
		            				String source = fixMessageObject.getField(49);
		            				String dest = fixMessageObject.getField(56);
		            				// FIXME "bad" users - specific to the dataset February 2019 
		            				if(source != null && (source.equalsIgnoreCase("NGALL1FX02") ||
		            				source.equalsIgnoreCase("NGALL1FX01") || source.equalsIgnoreCase("NGALL2FX01"))){
		            					fixMessageObject = null;
		            				}else if(dest != null && (dest.equalsIgnoreCase("NGALL1FX02") ||
				            		dest.equalsIgnoreCase("NGALL1FX01") || dest.equalsIgnoreCase("NGALL2FX01"))){
		            					fixMessageObject = null;
		            				}
		            			}catch(Exception e){
		            				// There has been an error parsing the string into a FIX message
		            				wrongMessages++;
		            			}
		            			if(fixMessageObject != null && fixMessageObject.getField(35) != null){
		            				fixMessages.add(fixMessageObject);
		            				correctFIXMessages++;
		            			}
		            			li = ls;
		            		}
		            		/* FIX message has been divided in at least two TCP segments, 
	            			take the information and save it for the next iteration when checking next TCP segment */
		            		if(accumFlag == false || (accumFlag == true && accumIPAddress == tcpPacket.getSourceIP())){
		            			accumPayload = tcpPayload.length() > li ? tcpPayload.substring(li) : null;
		            		}
		            		if(accumPayload != null && accumFlag == false){
		            			accumFlag = true;
		            			accumIPAddress = tcpPacket.getSourceIP(); // catch IṔ address to know from where to take the next piece
		            		}
			            }
			        }			
	                return true;
	            }
			});
		}catch(Exception e){
			e.printStackTrace();
		}finally{
			pcap.close();
			finish();
		}
	}
	
	public static void finish() throws FileNotFoundException, UnsupportedEncodingException{
		System.out.println("TCP Segments = " + tcpSegments);
		System.out.println("Total FIX Messages = " + totalFIXMessages);
		System.out.println("Valid FIX Messages = " + correctFIXMessages);
	}


}
