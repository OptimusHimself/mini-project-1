package com.example;

import com.aliyun.fc.runtime.Context;
import com.aliyun.fc.runtime.StreamRequestHandler;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.stream.Collectors;

public class ResultUpdateHandler implements StreamRequestHandler {
    
    @Override
    public void handleRequest(InputStream input, OutputStream output, Context context) throws java.io.IOException {
        context.getLogger().info("Result Update Function triggered");
        
        String requestBody = new BufferedReader(new InputStreamReader(input))
            .lines().collect(Collectors.joining("\n"));
        context.getLogger().info("Received update request: " + requestBody);
        
        String submissionId = (requestBody, "submission_id");
        String status = extractJsonValue(requestBody, "status");
        String note = extractJsonValue(requestBody, "note");
        
        if (submissionId == null || submissionId.isEmpty() || status == null) {
            String errorResponse = "{\"error\": \"Missing submission_id or status\"}";
            output.write(errorResponse.getBytes());
            return;
        }
        
        String dataServiceUrl = System.getenv().getOrDefault("DATA_SERVICE_URL",  
            "http://localhost:8000/api/submissions/update");
        
        String updatePayload = "{\"submission_id\":\"" + submissionId + 
                               "\",\"status\":\"" + status + 
                               "\",\"note\":\"" + escapeJson(note) + 
                               "\",\"updated_at\":\"" + System.currentTimeMillis() + "\"}";
        
        int dataServiceResponse = callDataService(dataServiceUrl, updatePayload, context);
        
        String response = "{\"message\":\"Result updated successfully\"," +
                          "\"submission_id\":\"" + submissionId + "\"," +
                          "\"status\":\"" + status + "\"," +
                          "\"data_service_response_code\":" + dataServiceResponse + "}";
        output.write(response.getBytes());
        
        context.getLogger().info("Response sent: " + response);
    }
    
    private int callDataService(String urlString, String payload, Context context) {
        try {
            URL url = new URL(urlString);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(30000);
            conn.setReadTimeout(30000);
            
            try (OutputStreamWriter writer = new OutputStreamWriter(conn.getOutputStream())) {
                writer.write(payload);
                writer.flush();
            }
            
            int responseCode = conn.getResponseCode();
            context.getLogger().info("Data Service response code: " + responseCode);
            return responseCode;
        } catch (Exception e) {
            context.getLogger().error("Failed to call Data Service: " + e.getMessage());
            return 500;
        }
    }
    
    private String extractJsonValue(String json, String key) {
        String searchKey = "\"" + key + "\":";
        int keyIndex = json.indexOf(searchKey);
        if (keyIndex == -1) return null;
        
        int startQuote = json.indexOf("\"", keyIndex + searchKey.length());
        if (startQuote == -1) return null;
        
        int endQuote = json.indexOf("\"", startQuote + 1);
        if (endQuote == -1) return null;
        
        return json.substring(startQuote + 1, endQuote);
    }
    
    private String escapeJson(String str) {
        if (str == null) return "";
        return str.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}