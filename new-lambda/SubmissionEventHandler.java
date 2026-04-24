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

public class SubmissionEventHandler implements StreamRequestHandler {
    
    @Override
    public void handleRequest(InputStream input, OutputStream output, Context context) throws java.io.IOException {
        context.getLogger().info("Submission Event Function triggered");
        
        String requestBody = new BufferedReader(new InputStreamReader(input))
            .lines().collect(Collectors.joining("\n"));
        context.getLogger().info("Received request: " + requestBody);
        
        String submissionId = extractJsonValue(requestBody, "submission_id");
        String title = extractJsonValue(requestBody, "title");
        String description = extractJsonValue(requestBody, "description");
        String posterFilename = extractJsonValue(requestBody, "poster_filename");
        
        if (submissionId == null || submissionId.isEmpty()) {
            String errorResponse = "{\"error\": \"Missing submission_id\"}";
            output.write(errorResponse.getBytes());
            return;
        }
        
        String payload = "{\"submission_id\":\"" + submissionId + 
                         "\",\"title\":\"" + escapeJson(title) + 
                         "\",\"description\":\"" + escapeJson(description) + 
                         "\",\"poster_filename\":\"" + escapeJson(posterFilename) + "\"}";
        
        String processingUrl = System.getenv().getOrDefault("PROCESSING_FUNCTION_URL", 
            "https://your-processing-function-url/invoke");
        
        String processingResult = callFunction(processingUrl, payload, context);
        
        String response = "{\"message\":\"Processing triggered\",\"submission_id\":\"" + 
                          submissionId + "\",\"result\":" + processingResult + "}";
        output.write(response.getBytes());
        
        context.getLogger().info("Response sent: " + response);
    }
    
    private String callFunction(String urlString, String payload, Context context) {
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
            context.getLogger().info("Called function, response code: " + responseCode);
            
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()))) {
                return reader.lines().collect(Collectors.joining("\n"));
            }
        } catch (Exception e) {
            context.getLogger().error("Failed to call function: " + e.getMessage());
            return "{\"error\":\"Failed to trigger processing\"}";
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